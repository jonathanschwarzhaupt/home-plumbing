from typing import Optional
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TursoConfig(BaseSettings):
    db_path: Path
    sync_url: Optional[str] = None
    auth_token: Optional[str] = None

    @field_validator("db_path")
    def validate_db_path(cls, v):
        Path(v).parent.mkdir(parents=True, exist_ok=True)
        Path(v).touch()
        return v

    model_config = SettingsConfigDict(env_prefix="TURSO_")
