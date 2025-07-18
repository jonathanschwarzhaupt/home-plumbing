import logging
from pathlib import Path
import pendulum
from pendulum import Date

from plumbing_core.sources.comdirect import (
    AccountTransaction,
    AccountBalance,
    APIConfig,
    authenticate_user_credentials,
    get_accounts_balances,
    get_session_id,
    get_transaction_data_paginated,
)
from plumbing_core.destinations.sqlite import (
    SQLiteConfig,
    write_account_transactions_booked,
    get_max_date_string,
)


def main() -> None:
    """Test the full auth flow and print all account transactions for one account reading the config from a .env file"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    cfg = APIConfig(_env_file=".env")
    session_id = get_session_id()

    access_token = authenticate_user_credentials(cfg=cfg, session_id=session_id)
    if not access_token:
        raise ValueError("No access token found")

    account_balances: list[AccountBalance] = get_accounts_balances(
        cfg=cfg, bearer_access_token=access_token.bearer_access_token
    )

    for account in account_balances:
        # Set default from when to fetch transactions
        last_transaction_date = Date(2025, 6, 1)
        account_id = account.account_id

        db_path = Path.cwd() / "comdirect.db"
        db_config = SQLiteConfig(db_path=db_path)

        # Step 1: Get max date from existing transactions table
        logging.info(f"Getting max date for account: '{account_id}'")
        max_date = get_max_date_string(
            config=db_config,
            table_name="account_transactions__booked",
            date_field="booking_date",
            filter_condition=f"account_id = '{account_id}'",
        )
        if max_date:
            last_transaction_date = pendulum.parse(max_date).date()

        logging.info(f"Getting data from date: '{last_transaction_date}'")
        transactions: list[AccountTransaction] = get_transaction_data_paginated(
            cfg=cfg,
            account_id=account_id,
            bearer_access_token=access_token.bearer_access_token,
            last_transaction_date=last_transaction_date,
            transaction_state="BOOKED",
        )

        record_count = write_account_transactions_booked(
            transactions=transactions, account_id=account_id, config=db_config
        )
        logging.info(f"Loaded {record_count} records")

    logging.info("All done")


if __name__ == "__main__":
    main()
