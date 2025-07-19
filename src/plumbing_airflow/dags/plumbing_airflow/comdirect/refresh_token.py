"""
# Comdirect Access Token Refresh DAG

Automatically refreshes Comdirect access tokens before they expire to maintain API connectivity.

## Overview

This DAG monitors and refreshes Comdirect OAuth access tokens:
1. Checks if the current access token needs refreshing
2. Calls the refresh token API endpoint if refresh is needed
3. Updates the stored token in Airflow Variables
4. Skips execution if token is still valid

## Schedule

- **Frequency**: Every 2 minutes (`*/2 * * * *`)
- **Purpose**: Proactive token management to prevent API authentication failures

## Tasks

- `refresh_auth_token`: Checks token expiry and refreshes if necessary
- `save_auth_token`: Updates the refreshed token in Airflow Variables

## Token Management

- **Refresh Logic**: Only refreshes tokens that are close to expiration
- **Skip Behavior**: Uses `AirflowSkipException` when refresh is not needed
- **Storage**: Updated tokens are stored in Airflow Variable `comdirect_access_token`

## Requirements

- Valid refresh token in existing access token data
- API configuration with client credentials
- Network connectivity to Comdirect OAuth endpoints

## Error Handling

- Skips execution when token is still valid (not an error)
- Logs token expiration times for monitoring
- Fails gracefully if refresh API call fails
"""

from airflow.sdk import dag, task
from airflow.exceptions import AirflowSkipException
from plumbing_core.sources.comdirect import refresh_token
from plumbing_airflow.shared.dag_config import (
    get_default_dag_args,
    get_comdirect_tags,
    get_api_config,
    get_auth_token,
    save_auth_token,
    create_access_token,
)
from typing import Dict, Any
import logging


@dag(schedule="*/2 * * * *", tags=get_comdirect_tags("auth"), **get_default_dag_args())
def comdirect_access_token():
    """Refresh an existing comdirect access token"""

    @task
    def refresh_auth_token(access_token_json: Dict[str, Any]) -> Dict[str, Any]:
        access_token = create_access_token(access_token_json)

        if access_token.needs_refresh():
            logging.info("Token needs to be refreshed")
            cfg = get_api_config()
            access_token = refresh_token(cfg=cfg, token=access_token)
            logging.info(f"Token refreshed. Now expires at: {access_token.expires_at}")

            return access_token.to_dict()

        logging.info(
            f"Token does not need to be refreshed until {access_token.expires_at}"
        )
        raise AirflowSkipException

    access_token = get_auth_token()
    refreshed_access_token = refresh_auth_token(access_token)
    save_auth_token(access_token=refreshed_access_token)


comdirect_access_token()
