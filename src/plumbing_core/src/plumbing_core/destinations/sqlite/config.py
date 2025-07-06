from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SQLiteConfig(BaseSettings):
    db_path: Path

    @field_validator("db_path")
    def validate_db_path(cls, v):
        Path(v).parent.mkdir(parents=True, exist_ok=True)
        Path(v).touch()
        return v

    model_config = SettingsConfigDict(env_prefix="SQLITE_")
