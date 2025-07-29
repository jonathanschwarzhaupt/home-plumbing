import libsql
import logging
from contextlib import contextmanager

from .config import TursoConfig

logger = logging.getLogger(__name__)


@contextmanager
def get_turso_connection(config: TursoConfig):
    """Turso connection optional embedded replica option for remote syncing"""

    conn = None

    try:
        if is_embedded_replica(config):
            conn = libsql.connect(
                str(config.db_path),
                sync_url=config.sync_url,
                auth_token=config.auth_token,
            )
            logger.debug(f"Connected to embedded SQLite database at '{config.db_path}'")
            yield conn

        else:
            conn = libsql.connect(str(config.db_path))
            logger.debug(f"Connected to SQLite database at '{config.db_path}'")
            yield conn

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

    finally:
        if conn:
            conn.close()


def is_embedded_replica(config: TursoConfig) -> bool:
    """Returns true if remote connection can be enabled, else false"""
    if config.sync_url and config.auth_token:
        return True

    return False
