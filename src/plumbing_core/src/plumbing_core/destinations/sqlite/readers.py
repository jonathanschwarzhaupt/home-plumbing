import logging
from typing import Optional

from .config import SQLiteConfig
from .connection import get_duckdb_connection


logger = logging.getLogger(__name__)


def get_max_date_string(
    config: SQLiteConfig,
    table_name: str,
    date_field: str,
    filter_condition: Optional[str],
) -> Optional[str]:
    """Gets the max date (string) from table name"""

    result = None
    where_sql = ""

    if filter_condition:
        where_sql = "WHERE " + filter_condition

    with get_duckdb_connection(config.db_path) as conn:
        table_exists = (
            conn.execute(
                f"""
                SELECT COUNT(*) FROM main.sqlite_master
                WHERE type='table' AND name='{table_name}'
                """
            ).fetchone()[0]
            > 0
        )

        if not table_exists:
            logging.info("Table does not exist. Returning 'None'")

            return result

        result = conn.execute(
            f"""
            SELECT MAX({date_field})
            FROM sqlite_db.{table_name}
            {where_sql}
            """
        ).fetchone()[0]
        logging.info(f"Max value for '{date_field}' = '{result}'")

        return result
