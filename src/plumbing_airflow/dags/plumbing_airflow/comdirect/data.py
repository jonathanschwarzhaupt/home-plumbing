"""
# Comdirect Data Extraction DAG

Regularly fetches and stores Comdirect account balances and transaction data (booked and notbooked) into Turso SQLite embedded replica.

## Overview

This DAG performs comprehensive data extraction from Comdirect banking API:
1. Retrieves current account balances for all accounts
2. Fetches booked transactions (incremental updates based on last booking date)
3. Fetches not-booked/pending transactions (full refresh)
4. Stores all data in SQLite database tables synced to its remote

## Schedule

- **Frequency**: Every hour (`0 * * * *`)
- **Purpose**: Keep financial data up-to-date for analysis and reporting

## Tasks

- `get_account_balances_data`: Fetches current balances and returns account IDs
- `get_account_transactions_data_booked`: Incremental sync of booked transactions
- `get_account_transactions_data_not_booked`: Full refresh of pending transactions

## Database Tables

- `account_balances`: Current account balance snapshots
- `account_transactions__booked`: Confirmed/settled transactions
- `account_transactions__not_booked`: Pending/unconfirmed transactions

## Requirements

- Valid access token in Airflow Variable `comdirect_access_token`
- Environment variables: `COMDIRECT__TURSO_PATH`, `TURSO_SYNC_URL`, and `TURSO_AUTH_TOKEN`
- Turso account for embedded sqlite replicas that sync to their remote

## Data Flow

1. **Balance Extraction**: Fetches all account balances and stores them
2. **Transaction Sync**: For each account, performs incremental sync of booked transactions
3. **Pending Transactions**: Refreshes all pending transactions across accounts
"""

from airflow.sdk import dag, task

from plumbing_core.sources.comdirect import (
    AccountBalance,
    get_accounts_balances,
    AccountTransaction,
    get_transaction_data_paginated,
    COMDIRECT_SCHEMAS,
)
from plumbing_core.destinations.turso import (
    TursoConfig,
    write_account_balances,
    write_account_transactions_booked,
    write_account_transactions_not_booked,
    get_max_date_string,
)
from plumbing_airflow.shared.dag_config import (
    get_default_dag_args,
    get_comdirect_tags,
    get_api_config,
    get_database_config,
    get_auth_token,
    create_access_token,
    DEFAULT_TRANSACTION_DATE,
)

import logging
import pendulum
from typing import Dict, Any, List


@dag(schedule="0 * * * *", tags=get_comdirect_tags("data"), **get_default_dag_args())
def comdirect_data():
    """Regularly fetches and inserts comdirect account balance and account transaction data into db"""

    @task
    def get_account_balances_data(
        access_token_json: Dict[str, Any],
    ) -> List[str]:
        """Gets account balances data"""

        access_token = create_access_token(access_token_json)
        cfg = get_api_config(use_env_file=True)

        account_balances: list[AccountBalance] = get_accounts_balances(
            cfg=cfg, bearer_access_token=access_token.bearer_access_token
        )

        logging.info("Loading to sqlite")
        db_config: TursoConfig = get_database_config(db_type="turso")
        record_count = write_account_balances(
            balances=account_balances,
            config=db_config,
            ddl=COMDIRECT_SCHEMAS["account_balances"],
        )
        logging.info(f"Loaded {record_count} records")

        return [account.account_id for account in account_balances]

    @task
    def get_account_transactions_data_booked(
        access_token_json: Dict[str, Any], account_ids: List[str]
    ) -> None:
        """Gets account transactions data"""

        access_token = create_access_token(access_token_json)
        cfg = get_api_config(use_env_file=True)
        db_config: TursoConfig = get_database_config(db_type="turso")
        table_name = "account_transactions__booked"

        for account_id in account_ids:
            # Set default from when to fetch transactions
            last_transaction_date = DEFAULT_TRANSACTION_DATE

            # Step 1: Get max date from existing transactions table
            logging.info(f"Getting max date for account: '{account_id}'")
            max_date = get_max_date_string(
                config=db_config,
                table_name=table_name,
                date_field="booking_date",
                filter_condition=f"account_id = '{account_id}'",
            )
            if max_date:
                logging.info("Found existing max date")
                last_transaction_date = pendulum.parse(max_date).date()

            # Step 2: Get and save booked transactions
            logging.info(f"Getting data from date: '{last_transaction_date}'")
            transactions: list[AccountTransaction] = get_transaction_data_paginated(
                cfg=cfg,
                account_id=account_id,
                bearer_access_token=access_token.bearer_access_token,
                last_transaction_date=last_transaction_date,
                transaction_state="BOOKED",
            )

            record_count = write_account_transactions_booked(
                transactions=transactions,
                account_id=account_id,
                config=db_config,
                ddl=COMDIRECT_SCHEMAS[table_name],
            )
            logging.info(f"Loaded {record_count} records to booked transactions table")

        logging.info("All done")

    @task
    def get_account_transactions_data_not_booked(
        access_token_json: Dict[str, Any], account_ids: List[str]
    ) -> None:
        """Gets account transactions data"""

        access_token = create_access_token(access_token_json)
        cfg = get_api_config(use_env_file=True)
        db_config: TursoConfig = get_database_config(db_type="turso")
        table_name = "account_transactions__not_booked"

        for account_id in account_ids:
            last_transaction_date = DEFAULT_TRANSACTION_DATE

            logging.info(f"Getting data for account: '{account_id}'")
            transactions: list[AccountTransaction] = get_transaction_data_paginated(
                cfg=cfg,
                account_id=account_id,
                bearer_access_token=access_token.bearer_access_token,
                last_transaction_date=last_transaction_date,
                transaction_state="NOTBOOKED",
            )

            record_count = write_account_transactions_not_booked(
                transactions=transactions,
                account_id=account_id,
                config=db_config,
                table_name=table_name,
                delete_keys=["account_id"],
                ddl=COMDIRECT_SCHEMAS[table_name],
            )
            logging.info(
                f"Loaded {record_count} records to not-booked transactions table"
            )

        logging.info("All done")

    access_token = get_auth_token()
    account_ids = get_account_balances_data(access_token)
    get_account_transactions_data_booked(
        access_token_json=access_token, account_ids=account_ids
    )
    get_account_transactions_data_not_booked(
        access_token_json=access_token, account_ids=account_ids
    )


comdirect_data()
