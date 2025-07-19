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
