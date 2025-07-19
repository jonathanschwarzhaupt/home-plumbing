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
