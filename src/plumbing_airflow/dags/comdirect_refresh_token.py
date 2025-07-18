from airflow.sdk import dag, task, Variable
from airflow.exceptions import AirflowSkipException
from plumbing_core.sources.comdirect import (
    APIConfig,
    AccessToken,
    refresh_token,
)
from typing import Dict, Any
from pendulum import datetime
import logging


@dag(
    start_date=datetime(2025, 4, 1), schedule="*/2 * * * *", tags=["comdirect", "auth"]
)
def comdirect_access_token():
    """Refresh an existing comdirect access token"""

    @task
    def get_auth_token() -> Dict[str, Any]:
        access_token_json = Variable.get(
            key="comdirect_access_token", deserialize_json=True
        )

        return access_token_json

    @task
    def refresh_auth_token(access_token_json: Dict[str, Any]) -> Dict[str, Any]:
        access_token = AccessToken(**access_token_json)

        if access_token.needs_refresh():
            logging.info("Token needs to be refreshed")
            cfg = APIConfig()
            access_token = refresh_token(cfg=cfg, token=access_token)
            logging.info(f"Token refreshed. Now expires at: {access_token.expires_at}")

            return access_token.to_dict()

        logging.info(
            f"Token does not need to be refreshed until {access_token.expires_at}"
        )
        raise AirflowSkipException

    @task
    def set_auth_token(access_token: Dict[str, Any]) -> None:
        logging.info("Trying to set Variable")
        Variable.set(
            key="comdirect_access_token", value=access_token, serialize_json=True
        )

    access_token = get_auth_token()
    refreshed_access_token = refresh_auth_token(access_token)
    set_auth_token(access_token=refreshed_access_token)


comdirect_access_token()
