import logging
from datetime import date

from plumbing_core.sources.comdirect import (
    AccountBalance,
    APIConfig,
    authenticate_user_credentials,
    get_accounts_balances,
    get_session_id,
    get_transaction_data_paginated,
)
from plumbing_core.sources.comdirect.types import AccountTransaction


def main() -> None:
    """Test the full auth flow and print all account balances reading the config from a .env file"""
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
    account_id = account_balances[0].account_id

    transactions: list[AccountTransaction] = get_transaction_data_paginated(
        cfg=cfg,
        account_id=account_id,
        bearer_access_token=access_token.bearer_access_token,
        last_transaction_date=date(2025, 5, 1),
        transaction_state="BOOKED",
    )
    print("Transactions:")
    for transaction in transactions:
        print(transaction.model_dump())
        print("----")


if __name__ == "__main__":
    main()
