from airflow.sdk import dag, task, Variable
from plumbing_core.sources.comdirect import (
    APIConfig,
    AccessToken,
    get_session_id,
    authenticate_user_credentials,
)
from typing import Dict, Any
from pendulum import datetime
import logging


@dag(start_date=datetime(2025, 4, 1), schedule=None, tags=["comdirect", "auth"])
def comdirect_auth():
    """Authenticate client against comdirect"""

    @task
    def get_auth_token() -> Dict[str, Any]:
        cfg = APIConfig()
        session_id = get_session_id()
        access_token: AccessToken = authenticate_user_credentials(
            cfg=cfg, session_id=session_id
        )
        return access_token.to_dict()

    @task
    def save_auth_token(access_token) -> None:
        logging.info("Trying to set Variable")
        Variable.set(
            key="comdirect_access_token", value=access_token, serialize_json=True
        )

    access_token = get_auth_token()
    save_auth_token(access_token)


comdirect_auth()
