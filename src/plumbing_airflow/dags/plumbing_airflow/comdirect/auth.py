"""
# Comdirect Authentication DAG

This DAG handles the initial OAuth 2.0 authentication flow with Comdirect banking API.

## Overview

The authentication process follows Comdirect's multi-step OAuth flow:
1. Generate session ID
2. Authenticate with user credentials
3. Handle PhotoTan challenge (manual confirmation required)
4. Obtain access token for API calls

## Schedule

- **Trigger**: Manual only (no automatic schedule)
- **Purpose**: One-time authentication or re-authentication when tokens expire

## Tasks

- `get_auth_token`: Performs OAuth flow and returns access token
- `save_auth_token`: Stores token in Airflow Variables for use by other DAGs

## Requirements

- Environment variables: `COMDIRECT_CLIENT_ID`, `COMDIRECT_CLIENT_SECRET`, `COMDIRECT_USERNAME`, `COMDIRECT_PASSWORD`
- Manual PhotoTan confirmation during execution

## Output

Stores access token in Airflow Variable `comdirect_access_token` for downstream DAGs.
"""

from airflow.sdk import dag, task
from plumbing_core.sources.comdirect import (
    get_session_id,
    authenticate_user_credentials,
)
from plumbing_airflow.shared.dag_config import (
    get_default_dag_args,
    get_comdirect_tags,
    get_api_config,
    save_auth_token,
)
from typing import Dict, Any


@dag(schedule=None, tags=get_comdirect_tags("auth"), **get_default_dag_args())
def comdirect_auth():
    """Authenticate client against comdirect"""

    @task
    def get_auth_token() -> Dict[str, Any]:
        cfg = get_api_config()
        session_id = get_session_id()
        access_token = authenticate_user_credentials(cfg=cfg, session_id=session_id)
        return access_token.to_dict()

    access_token = get_auth_token()
    save_auth_token(access_token)


comdirect_auth()
