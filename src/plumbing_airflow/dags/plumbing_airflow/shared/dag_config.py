"""Shared DAG configuration and utilities for Comdirect workflows."""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Literal
from pendulum import datetime, Date

from airflow.sdk import task, Variable, Asset
from plumbing_core.destinations.turso import TursoConfig
from plumbing_core.sources.comdirect import APIConfig, AccessToken
from plumbing_core.destinations.sqlite import SQLiteConfig


# Constants
DEFAULT_START_DATE = datetime(2025, 4, 1)
COMDIRECT_ACCESS_TOKEN_KEY = "comdirect_access_token"
DEFAULT_TRANSACTION_DATE = Date(2025, 1, 1)
TRANSACTION_ASSET = Asset(
    "comdirect_transactions__booked", extra={"source": "comdirect"}
)


def get_default_dag_args() -> Dict[str, Any]:
    """Get default DAG arguments for Comdirect workflows."""
    import inspect

    caller_module = inspect.getmodule(inspect.stack()[1][0])
    return {
        "start_date": DEFAULT_START_DATE,
        "default_args": {
            "owner": "Jonathan",
        },
        "max_consecutive_failed_dag_runs": 5,
        "doc_md": caller_module.__doc__
        if caller_module and caller_module.__doc__
        else None,
    }


def get_comdirect_tags(workflow_type: str) -> list[str]:
    """Get standardized tags for Comdirect DAGs."""
    base_tags = ["comdirect"]

    if workflow_type == "auth":
        return base_tags + ["auth"]
    elif workflow_type == "data":
        return base_tags + ["data"]
    else:
        return base_tags


@task
def get_auth_token() -> Dict[str, Any]:
    """Reusable task to get authentication token from Airflow Variables."""
    access_token_json = Variable.get(
        key=COMDIRECT_ACCESS_TOKEN_KEY, deserialize_json=True
    )
    return access_token_json


@task
def save_auth_token(access_token: Dict[str, Any]) -> None:
    """Reusable task to save authentication token to Airflow Variables."""
    logging.info("Trying to set Variable")
    Variable.set(
        key=COMDIRECT_ACCESS_TOKEN_KEY, value=access_token, serialize_json=True
    )


def get_api_config(use_env_file: bool = False) -> APIConfig:
    """Get standardized API configuration."""
    if use_env_file:
        return APIConfig(_env_file=".env")
    return APIConfig()


def get_database_config(
    db_type: Literal["sqlite", "turso"],
) -> SQLiteConfig | TursoConfig:
    """Get standardized database configuration."""

    if db_type == "sqlite":
        db_path = Path(os.environ["COMDIRECT__SQLITE_PATH"]) / "comdirect.db"
        return SQLiteConfig(db_path=db_path)
    elif db_type == "turso":
        db_path = Path(os.environ["COMDIRECT__TURSO_PATH"]) / "comdirect_turso.db"
        return TursoConfig(db_path=db_path)
    else:
        raise ValueError("db_type must be either 'sqlite' or 'turso'")


def create_access_token(access_token_json: Dict[str, Any]) -> AccessToken:
    """Create AccessToken instance from JSON data."""
    return AccessToken(**access_token_json)
