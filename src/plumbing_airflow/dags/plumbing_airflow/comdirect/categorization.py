"""
# Comdirect Transaction Categorization DAG
"""

import logging
import logfire

from airflow.sdk import dag, task
from airflow.exceptions import AirflowSkipException

from plumbing_core.processors.categorization import (
    PydanticAIConfig,
    get_comdirect_transaction_categorization_agent,
    CategorizedBankTransaction,
    categorize_transaction,
    CATEGORIZED_BANK_TRANSACTION_DDL,
)
from plumbing_core.destinations.turso import (
    get_transactions_to_categorize,
    write_account_transactions_categorized,
)
from plumbing_airflow.shared.dag_config import (
    TRANSACTION_ASSET,
    get_default_dag_args,
    get_comdirect_tags,
    get_database_config,
)


@dag(
    schedule=TRANSACTION_ASSET,
    tags=get_comdirect_tags("data"),
    **get_default_dag_args(),
)
def comdirect_categorization():
    """Fetches and inserts comdirect account balance and account transaction data into db"""

    @task(inlets=[TRANSACTION_ASSET])
    def categorize(inlet_events):
        # Get the asset's events from context
        asset_events = inlet_events[TRANSACTION_ASSET]
        if len(asset_events) == 0:
            print(f"No asset_events for {TRANSACTION_ASSET.uri}")

        last_row_count = asset_events[-1].extra["row_count"]
        if last_row_count == 0:
            raise AirflowSkipException("No new transactions to categorize")

        logging.info(
            f"Received asset event to categorize {last_row_count} transactions"
        )

        # Get data step
        db_config = get_database_config(db_type="turso")
        transactions = get_transactions_to_categorize(config=db_config)
        # well, just to be sure
        if not transactions:
            logging.info("No transactions to categorize")
            raise AirflowSkipException

        ai_config = PydanticAIConfig()
        agent = get_comdirect_transaction_categorization_agent(
            config=ai_config, output_type=CategorizedBankTransaction
        )

        # Process data step
        logfire.configure(
            send_to_logfire="if-token-present",  # only send to logfire if token is present in env
            service_name="plumbing-airflow",
        )
        logfire.instrument_pydantic_ai()  # capture pydantic ai spans and traces
        logfire.instrument_httpx(
            capture_all=True
        )  # and the http requests made to the model providers

        logging.info(f"Starting categorization for {len(transactions)} transactions")
        categorized_transactions = []
        for transaction in transactions:
            res = categorize_transaction(agent=agent, transaction=transaction)
            if res:
                categorized_transactions.append(res)

        logging.info(
            f"Finished categorization for {len(categorized_transactions)} transactions"
        )

        # Save data step
        inserted_count = write_account_transactions_categorized(
            categorized_transactions=categorized_transactions,
            config=db_config,
            ddl=CATEGORIZED_BANK_TRANSACTION_DDL,
        )
        logging.info(f"Inserted {inserted_count} records")

    categorize()


comdirect_categorization()
