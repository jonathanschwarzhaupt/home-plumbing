import logging
from typing import List

from pydantic import BaseModel

from plumbing_core.processors.categorization.types import CategorizedBankTransaction
from plumbing_core.sources.comdirect import (
    AccountBalance,
    AccountTransaction,
)
from .config import TursoConfig
from .connection import get_turso_connection, is_embedded_replica

logger = logging.getLogger(__name__)


def _ensure_table_exists(
    conn,
    table_name: str,
    ddl: str,
) -> None:
    """Ensure table schema exists in Turso database, create if needed"""

    table_exists = (
        conn.execute(
            f"""
            SELECT COUNT(*) FROM main.sqlite_master
            WHERE type='table' AND name='{table_name}'
            """
        ).fetchone()[0]
        > 0
    )

    is_staging_table = table_name.startswith("staging_")

    # For staging tables, drop and recreate; for regular tables, only create if not exists
    if is_staging_table or not table_exists:
        if is_staging_table:
            # Drop staging table if exists, then create new one
            conn.execute(f"DROP TABLE IF EXISTS main.{table_name}")
            create_table_str = f"CREATE TABLE main.{table_name}"
            logger.info(f"Dropped staging table {table_name}")
        else:
            create_table_str = f"CREATE TABLE IF NOT EXISTS main.{table_name}"
            logger.info(f"Creating new table {table_name}")

        logger.debug(
            f"Creating table {table_name} with statement: {create_table_str} and definition: {ddl}"
        )
        conn.execute(
            f"""
            {create_table_str}
            {ddl}
            """
        )
        logger.info(f"Created table {table_name}")
    else:
        logger.info(f"Table {table_name} already exists")


def _delete_and_insert(
    conn,
    data: List[BaseModel],
    table_name: str,
    delete_keys: List[str],
    ddl: str,
) -> int:
    """Delete existing records matching staging data and insert new data using staging table"""

    len_new_data = len(data)
    if len_new_data < 1:
        logger.info("No new data, returning")
        return 0

    if not delete_keys:
        raise ValueError("'delete_keys' is required.")

    staging_table_name = "staging_" + table_name

    # Create staging table and populate with new data
    # Create staging table schema
    _ensure_table_exists(conn=conn, table_name=staging_table_name, ddl=ddl)

    # Populate staging table with new data
    row_data = data[0].model_dump()
    columns = list(row_data.keys())
    columns_str = ", ".join(columns)
    placeholders = ", ".join(["?" for _ in columns])

    insert_sql = (
        f"INSERT INTO main.{staging_table_name} ({columns_str}) VALUES ({placeholders})"
    )
    logger.debug(f"Populating staging table with SQL: {insert_sql}")

    for row in data:
        row_values = list(row.model_dump(mode="json").values())
        conn.execute(insert_sql, row_values)
    logger.info(f"Populated staging table {staging_table_name} with {len(data)} rows")

    row_count_before = conn.execute(
        f"SELECT COUNT(*) FROM main.{table_name}"
    ).fetchone()[0]

    # Delete existing records that match staging data
    where_condition = " AND ".join(
        [
            f"main.{table_name}.{key} = main.{staging_table_name}.{key}"
            for key in delete_keys
        ]
    )
    delete_sql = f"""
        DELETE FROM main.{table_name}
        WHERE EXISTS (
            SELECT 1 FROM main.{staging_table_name}
            WHERE {where_condition}
        )
    """
    logger.debug(f"Executing DELETE: {delete_sql}")
    conn.execute(delete_sql)
    logger.info(f"Executed DELETE for records matching {len_new_data} staged rows")

    # Insert all records from staging table
    insert_sql = f"""
        INSERT INTO main.{table_name}
        SELECT * FROM main.{staging_table_name}
    """
    logger.debug(f"Executing INSERT: {insert_sql}")
    conn.execute(insert_sql)

    # Clean up staging table
    logger.debug("Dropping staging table")
    conn.execute(f"DROP TABLE IF EXISTS main.{staging_table_name}")

    row_count_after = conn.execute(
        f"SELECT COUNT(*) FROM main.{table_name}"
    ).fetchone()[0]

    conn.commit()
    logger.info("Completed transaction")
    logger.info(
        f"Inserted {len_new_data} new records (net change: {row_count_after - row_count_before})"
    )

    return len_new_data


def _insert_if_not_exists(
    conn,
    data: List[AccountBalance] | List[AccountTransaction],
    table_name: str,
    on_conflict_keys: List[str],
    ddl: str,
) -> int:
    """Inserts new records if not exists"""

    staging_table_name = "staging_" + table_name

    if not on_conflict_keys:
        raise ValueError("'on_conflict_keys' is required.")

    # Create staging table schema
    _ensure_table_exists(conn=conn, table_name=staging_table_name, ddl=ddl)

    # Populate staging table with new data
    row_data = data[0].model_dump()
    columns = list(row_data.keys())
    columns_str = ", ".join(columns)
    placeholders = ", ".join(["?" for _ in columns])

    insert_sql = (
        f"INSERT INTO main.{staging_table_name} ({columns_str}) VALUES ({placeholders})"
    )
    logger.debug(f"Populating staging table with SQL: {insert_sql}")

    for row in data:
        row_values = list(row.model_dump(mode="json").values())
        conn.execute(insert_sql, row_values)
    logger.info(f"Populated staging table {staging_table_name} with {len(data)} rows")

    row_count_before = conn.execute(
        f"SELECT COUNT(*) FROM main.{table_name}"
    ).fetchone()[0]

    # Filter incoming data to only new data
    where_condition = " AND ".join(
        [
            f"main.{table_name}.{key} = main.{staging_table_name}.{key}"
            for key in on_conflict_keys
        ]
    )

    # 'INSERT INTO SELECT *'
    insert_sql = f"""
        INSERT INTO main.{table_name}
        SELECT * FROM main.{staging_table_name}
        WHERE NOT EXISTS (
            SELECT 1 FROM main.{table_name}
            WHERE {where_condition}
        )
    """
    logger.debug(f"Executing INSERT: {insert_sql}")
    conn.execute(insert_sql)

    logger.debug("Dropping staging table")
    conn.execute(f"DROP TABLE IF EXISTS main.{staging_table_name}")

    row_count_after = conn.execute(
        f"SELECT COUNT(*) FROM main.{table_name}"
    ).fetchone()[0]
    inserted_row_count = row_count_after - row_count_before
    logger.info(f"INSERTED {inserted_row_count} new records")

    conn.commit()
    logger.info("Completed transaction")

    return inserted_row_count


def write_account_balances(
    balances: List[AccountBalance],
    config: TursoConfig,
    ddl: str,
    table_name: str = "account_balances",
    delete_keys: List[str] = ["account_id", "_inserted_at_day"],
) -> int:
    """Write account balances using transactional delete+insert"""

    if not balances:
        logger.info("No balances passed, returning early")
        return 0

    with get_turso_connection(config) as conn:
        if is_embedded_replica(config):
            conn.sync()

        try:
            # Ensure table schema exists
            _ensure_table_exists(conn=conn, table_name=table_name, ddl=ddl)

            # Always use delete and insert strategy
            inserted_count = _delete_and_insert(
                conn=conn,
                data=balances,
                table_name=table_name,
                delete_keys=delete_keys,
                ddl=ddl,
            )

            if is_embedded_replica(config):
                conn.sync()

            return inserted_count

        except Exception as e:
            conn.rollback()

            if is_embedded_replica(config):
                conn.sync()

            logger.error(f"Transaction rolled back due to error: {e}")
            raise


def write_account_transactions_booked(
    transactions: List[AccountTransaction],
    account_id: str,
    config: TursoConfig,
    ddl: str,
    table_name: str = "account_transactions__booked",
    delete_keys: List[str] = ["account_id", "reference"],
) -> int:
    """Write account transactions using transactional 'insert if not exists'"""

    if not transactions:
        logger.info("No transactions passed, returning")
        return 0

    # Use model_copy to add account_id without pandas
    enhanced_transactions = [
        transaction.model_copy(update={"account_id": account_id})
        for transaction in transactions
    ]

    with get_turso_connection(config) as conn:
        try:
            if is_embedded_replica(config):
                conn.sync()

            # Ensure table schema exists
            _ensure_table_exists(conn=conn, table_name=table_name, ddl=ddl)

            # Always use insert if not exists strategy
            inserted_count = _insert_if_not_exists(
                conn=conn,
                data=enhanced_transactions,
                table_name=table_name,
                ddl=ddl,
                on_conflict_keys=delete_keys,
            )

            logger.info(f"Transaction commited: {inserted_count} records processesed")
            if is_embedded_replica(config):
                conn.sync()

            return inserted_count

        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise


def write_account_transactions_not_booked(
    transactions: List[AccountTransaction],
    account_id: str,
    config: TursoConfig,
    ddl: str,
    table_name: str = "account_transactions__not_booked",
    delete_keys: List[str] = ["account_id"],
) -> int:
    """Write not-booked account transactions using transactional 'delete+insert'"""

    if not transactions:
        logger.info("No transactions passed, returning")
        return 0

    # Use model_copy to add account_id without pandas
    enhanced_transactions = [
        transaction.model_copy(update={"account_id": account_id})
        for transaction in transactions
    ]

    with get_turso_connection(config) as conn:
        try:
            if is_embedded_replica(config):
                conn.sync()

            # Ensure table schema exists
            _ensure_table_exists(conn=conn, table_name=table_name, ddl=ddl)

            # Always use delete and insert strategy
            inserted_count = _delete_and_insert(
                conn=conn,
                data=enhanced_transactions,
                table_name=table_name,
                delete_keys=delete_keys,
                ddl=ddl,
            )

            logger.info(f"Transaction committed: {inserted_count} records processesed")
            if is_embedded_replica(config):
                conn.sync()

            return inserted_count

        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise


def write_account_transactions_categorized(
    categorized_transactions: List[CategorizedBankTransaction],
    config: TursoConfig,
    ddl: str,
    table_name: str = "account_transactions__categorized",
    delete_keys: List[str] = ["account_id", "reference"],
) -> int:
    if not categorized_transactions:
        logger.info("No categorized transactions passed, returning")
        return 0

    with get_turso_connection(config) as conn:
        try:
            if is_embedded_replica(config):
                conn.sync()

            _ensure_table_exists(conn=conn, table_name=table_name, ddl=ddl)

            inserted_count = _delete_and_insert(
                conn=conn,
                data=categorized_transactions,
                table_name=table_name,
                delete_keys=delete_keys,
                ddl=ddl,
            )
            logger.info(f"Transaction committed: {inserted_count} records processesed")

            if is_embedded_replica(config):
                conn.sync()

            return inserted_count

        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
