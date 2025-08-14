import logging
from typing import Optional, Dict, Any

from .config import TursoConfig
from .connection import get_turso_connection, is_embedded_replica


logger = logging.getLogger(__name__)


def get_max_date_string(
    config: TursoConfig,
    table_name: str,
    date_field: str,
    filter_condition: Optional[str],
) -> Optional[str]:
    """Gets the max date (string) from table name"""

    result = None
    where_sql = ""

    if filter_condition:
        where_sql = "WHERE " + filter_condition

    with get_turso_connection(config) as conn:
        if is_embedded_replica(config):
            conn.sync()

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
            logger.info("Table does not exist. Returning 'None'")

            return result

        result = conn.execute(
            f"""
            SELECT MAX({date_field})
            FROM main.{table_name}
            {where_sql}
            """
        ).fetchone()[0]
        logger.info(f"Max value for '{date_field}' = '{result}'")

        return result


def get_transactions_to_categorize(
    config: TursoConfig,
    source_table_name: str = "account_transactions__booked",
    categorization_table_name: str = "account_transactions__categorized",
    limit: Optional[int] = 10,
) -> Optional[list[Dict[str, Any]]]:
    """Gets the max date (string) from table name"""

    result = None

    with get_turso_connection(config) as conn:
        # Does the source table exist
        source_table_exists = (
            conn.execute(
                f"""
                SELECT COUNT(*) FROM main.sqlite_master
                WHERE type='table' AND name='{source_table_name}'
                """
            ).fetchone()[0]
            > 0
        )

        # No transactions to categorize - return
        if not source_table_exists:
            logging.info("Source table does not exist. Returning 'None'")
            return result
        logger.info("Source table exists")

        # Transactions table does exist, let's find the column names of the table
        columns = conn.execute(
            f"""
            SELECT name
            FROM PRAGMA_TABLE_INFO('{source_table_name}')
            """
        ).fetchall()
        columns = [elem[0] for elem in columns]
        logger.info(f"Obtained columns: '{columns}' from table '{source_table_name}'")

        # does the categorization table exist
        categorization_table_exists = (
            conn.execute(
                f"""
                SELECT COUNT(*) FROM main.sqlite_master
                WHERE type='table' AND name='{categorization_table_name}'
                """
            ).fetchone()[0]
            > 0
        )

        # No transactions were categorized yet
        if not categorization_table_exists:
            logger.info(
                f"Categorization table does not exist. Returning earliest {limit} transactions"
            )
            result = conn.execute(
                f"""
                SELECT *
                FROM main.{source_table_name}
                ORDER BY _inserted_at_ts DESC
                LIMIT 10
                """
            ).fetchall()
        # Some transactions were already categorized
        else:
            select_sql = f"""
                SELECT *
                FROM main.{source_table_name} t1
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM main.{categorization_table_name} t2
                    WHERE t1.account_id = t2.account_id
                        AND t1.reference = t2.reference
                )
                ORDER BY _inserted_at_ts DESC
                LIMIT 10
            """
            logger.info(f"Select SQL: {select_sql}")
            result = conn.execute(select_sql).fetchall()
            logger.info(
                f"Categorization table exists. Returning {limit} transactions not yet categorized"
            )

        if not result:
            logger.error("Unexpected error. Raising error")
            raise ValueError("Unexpected error obtaining transactions to categorize")

        return [dict(zip(columns, value_list)) for value_list in result]
