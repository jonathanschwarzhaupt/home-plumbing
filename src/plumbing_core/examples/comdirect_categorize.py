import logging
from pathlib import Path
from plumbing_core.destinations.turso import (
    TursoConfig,
    get_transactions_to_categorize,
    write_account_transactions_categorized,
)
from plumbing_core.processors.categorization import (
    PydanticAIConfig,
    get_comdirect_transaction_categorization_agent,
    CategorizedBankTransaction,
    categorize_transaction,
    CATEGORIZED_BANK_TRANSACTION_DDL,
)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    db_path = Path.cwd() / "comdirect_turso.db"
    db_config = TursoConfig(db_path=db_path)
    transactions = get_transactions_to_categorize(config=db_config)

    if not transactions:
        raise ValueError("No transactions")

    ai_config = PydanticAIConfig(_env_file=".env.pydanticai")
    agent = get_comdirect_transaction_categorization_agent(
        config=ai_config, output_type=CategorizedBankTransaction
    )

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


if __name__ == "__main__":
    main()
