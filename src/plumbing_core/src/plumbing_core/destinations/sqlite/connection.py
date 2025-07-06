import duckdb
from contextlib import contextmanager
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@contextmanager
def get_duckdb_connection(db_path: Path):
    """DuckDB connection with SQLite attachment"""

    conn = None
    try:
        conn = duckdb.connect()
        conn.execute(f"ATTACH '{db_path}' AS sqlite_db (TYPE sqlite)")
        logger.debug(f"Connected to SQLite database at '{db_path}'")
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()
