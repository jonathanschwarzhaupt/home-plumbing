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
    get_default_dag_args,
    get_comdirect_tags,
    get_database_config,
)


@dag(schedule=None, tags=get_comdirect_tags("data"), **get_default_dag_args())
def comdirect_categorization():
    """Regularly fetches and inserts comdirect account balance and account transaction data into db"""

    @task
    def categorize_transactions() -> None:
        # Get data step
        db_config = get_database_config(db_type="turso")
        transactions = get_transactions_to_categorize(config=db_config)
        if not transactions:
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

    categorize_transactions()


comdirect_categorization()
