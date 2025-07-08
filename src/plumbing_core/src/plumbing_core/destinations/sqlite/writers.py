import duckdb
import logging
import pendulum
import pandas as pd
from typing import List


from plumbing_core.sources.comdirect import AccountBalance, AccountTransaction
from .config import SQLiteConfig
from .connection import get_duckdb_connection

logger = logging.getLogger(__name__)


def _ensure_table_exists(
    conn: duckdb.DuckDBPyConnection, table_name: str, df: pd.DataFrame
) -> bool:
    """Ensure table exists in SQLite database, create if needed"""

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
        logger.info(f"Creating new table {table_name}")
        conn.execute(
            f"""
            CREATE TABLE sqlite_db.{table_name} AS
            FROM df
            """
        )
        return True

    logger.info(f"Table {table_name} already exists")
    return False


def _delete_and_insert(
    conn: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    table_name: str,
    delete_keys: List[str],
) -> int:
    """Delete existing records and insert new data"""

    if delete_keys:
        delete_conditions = []
        for _, row in df.iterrows():
            conditions = []
            for key in delete_keys:
                value = row[key]
                if pd.isna(value):
                    conditions.append(f"{key} IS NULL")
                elif isinstance(value, str):
                    escaped_value = str(value).replace("'", "''")
                    conditions.append(f"{key} = '{escaped_value}'")
                else:
                    conditions.append(f"{key} = {value}")

            if conditions:
                delete_conditions.append(f"({' AND '.join(conditions)})")

        if delete_conditions:
            where_clause = " OR ".join(delete_conditions)
            delete_sql = f"DELETE FROM sqlite_db.{table_name} WHERE {where_clause}"
            logger.debug(f"Executing DELETE: {delete_sql}")
            conn.execute(delete_sql)
            logger.info(f"Executed DELETE for {len(df)} key combinations")

    insert_sql = f"INSERT INTO sqlite_db.{table_name} FROM df"
    conn.execute(insert_sql)
    logger.info(f"Inserted {len(df)} new records")

    return len(df)


def _insert_if_not_exists(
    conn: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    table_name: str,
    on_conflict_keys: List[str],
) -> int:
    """Inserts new records if not exists"""

    inserted_row_count = len(df)

    if not on_conflict_keys:
        raise ValueError("'on_conflict_keys' is required.")

    # Filter incoming data to only new data
    where_condition = " AND ".join([f"t1.{key} = t2.{key}" for key in on_conflict_keys])
    filter_df_sql = f"""
        FROM df t1
        WHERE NOT EXISTS (
            SELECT 1 FROM
            sqlite_db.{table_name} t2
            WHERE {where_condition}
        )
    """
    try:
        df = conn.sql(filter_df_sql).df()
        inserted_row_count = len(df)
    except Exception as e:
        logger.error(f"Exception filtering incoming data with error: {e}")
        raise
    if inserted_row_count == 0:
        logger.info("No new data, returning")
        return 0

    # 'INSERT INTO SELECT *'
    insert_sql = f"""
        INSERT INTO sqlite_db.{table_name}
        FROM df
    """

    logger.debug(f"Executing INSERT: {insert_sql}")
    try:
        conn.execute(insert_sql)
    except Exception as e:
        logger.error(
            f"Exception insert where not exists for query: {insert_sql} with error: {e}"
        )
        raise
    logger.info(f"Inserted {inserted_row_count} new records")

    return inserted_row_count


def write_account_balances(
    balances: List[AccountBalance],
    config: SQLiteConfig,
    table_name: str = "account_balances",
    delete_keys: List[str] = ["account_id", "_inserted_at_day"],
) -> int:
    """Write account balances using transactional delete+insert"""

    if not balances:
        logger.info("No balances passed, returning early")
        return 0

    df = pd.DataFrame([balance.model_dump() for balance in balances])
    df["_inserted_at_day"] = pendulum.now("CET").to_date_string()
    df["_inserted_at_ts"] = pendulum.now("CET").to_datetime_string()

    with get_duckdb_connection(config.db_path) as conn:
        logger.info("Beginning transaction")
        conn.execute("BEGIN TRANSACTION")

        try:
            table_created = _ensure_table_exists(
                conn=conn, table_name=table_name, df=df
            )
            if table_created:
                inserted_count = len(df)
            else:
                inserted_count = _delete_and_insert(
                    conn=conn, df=df, table_name=table_name, delete_keys=delete_keys
                )

            conn.execute("COMMIT")
            logger.info(f"Transaction committed: {inserted_count} records processesed")
            return inserted_count

        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"Transaction rolled back due to error: {e}")
            raise


def write_account_transactions_booked(
    transactions: List[AccountTransaction],
    account_id: str,
    config: SQLiteConfig,
    table_name: str = "account_transactions__booked",
    delete_keys: List[str] = ["account_id", "reference"],
) -> int:
    """Write account transactions using transactional delete+insert"""

    if not transactions:
        logger.info("No transactions passed, returning")
        return 0

    df = pd.DataFrame([transaction.model_dump() for transaction in transactions])
    df["account_id"] = account_id
    df["_inserted_at_day"] = pendulum.now("CET").to_date_string()
    df["_inserted_at_ts"] = pendulum.now("CET").to_datetime_string()

    with get_duckdb_connection(config.db_path) as conn:
        logger.info("Beginning transaction")
        conn.execute("BEGIN TRANSACTION")

        try:
            table_created = _ensure_table_exists(
                conn=conn, table_name=table_name, df=df
            )
            if table_created:
                inserted_count = len(df)
            else:
                inserted_count = _insert_if_not_exists(
                    conn=conn,
                    df=df,
                    table_name=table_name,
                    on_conflict_keys=delete_keys,
                )

            conn.execute("COMMIT")
            logger.info(f"Transaction commited: {inserted_count} records processesed")
            return inserted_count

        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
