from airflow.sdk import dag, task, Variable
from plumbing_core.sources.comdirect import (
    APIConfig,
    get_session_id,
    authenticate_user_credentials,
)
from pendulum import datetime
import logging


@dag(start_date=datetime(2025, 4, 1), schedule=None, tags=["comdirect"])
def comdirect_auth():
    """Authenticate client against comdirect"""

    @task
    def get_auth_token():
        cfg = APIConfig()
        session_id = get_session_id()
        access_token = authenticate_user_credentials(cfg=cfg, session_id=session_id)
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
