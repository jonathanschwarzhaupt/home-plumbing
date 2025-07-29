import logging
from pathlib import Path
from pendulum import Date

from plumbing_core.sources.comdirect import (
    AccountTransaction,
    AccountBalance,
    APIConfig,
    authenticate_user_credentials,
    get_accounts_balances,
    get_session_id,
    get_transaction_data_paginated,
    COMDIRECT_SCHEMAS,
)
from plumbing_core.destinations.turso import (
    TursoConfig,
    write_account_transactions_booked,
)


def main() -> None:
    """Test the full auth flow and print all account transactions for one account reading the config from a .env file"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    cfg = APIConfig(_env_file=".env.comdirect")
    session_id = get_session_id()

    access_token = authenticate_user_credentials(cfg=cfg, session_id=session_id)
    if not access_token:
        raise ValueError("No access token found")

    account_balances: list[AccountBalance] = get_accounts_balances(
        cfg=cfg, bearer_access_token=access_token.bearer_access_token
    )

    for account in account_balances:
        account_id = account.account_id

        transactions: list[AccountTransaction] = get_transaction_data_paginated(
            cfg=cfg,
            account_id=account_id,
            bearer_access_token=access_token.bearer_access_token,
            last_transaction_date=Date(2025, 5, 1),
            transaction_state="BOOKED",
        )

        logging.info("Loading to turso sqlite")
        db_path = Path.cwd() / "comdirect_turso.db"
        db_config = TursoConfig(db_path=db_path)
        record_count = write_account_transactions_booked(
            transactions=transactions,
            account_id=account_id,
            config=db_config,
            ddl=COMDIRECT_SCHEMAS["account_transactions__booked"],
        )
        logging.info(f"Loaded {record_count} records")


if __name__ == "__main__":
    main()
