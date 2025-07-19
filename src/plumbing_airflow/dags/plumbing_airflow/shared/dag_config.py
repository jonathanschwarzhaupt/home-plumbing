"""Shared DAG configuration and utilities for Comdirect workflows."""

import os
import logging
from pathlib import Path
from typing import Dict, Any
from pendulum import datetime, Date

from airflow.sdk import task, Variable
from plumbing_core.sources.comdirect import APIConfig, AccessToken
from plumbing_core.destinations.sqlite import SQLiteConfig


# Constants
DEFAULT_START_DATE = datetime(2025, 4, 1)
COMDIRECT_ACCESS_TOKEN_KEY = "comdirect_access_token"
DEFAULT_TRANSACTION_DATE = Date(2025, 1, 1)


def get_default_dag_args() -> Dict[str, Any]:
    """Get default DAG arguments for Comdirect workflows."""
    return {
        "start_date": DEFAULT_START_DATE,
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


def get_database_config() -> SQLiteConfig:
    """Get standardized database configuration."""
    db_path = Path(os.environ["COMDIRECT__SQLITE_PATH"]) / "comdirect.db"
    return SQLiteConfig(db_path=db_path)


def create_access_token(access_token_json: Dict[str, Any]) -> AccessToken:
    """Create AccessToken instance from JSON data."""
    return AccessToken(**access_token_json)
