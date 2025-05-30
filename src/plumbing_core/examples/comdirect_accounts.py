import logging

from plumbing_core.sources.comdirect import (
    AccountBalance,
    APIConfig,
    authenticate_user_credentials,
    get_accounts_balances,
    get_session_id,
)


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
    print(account_balances[0].model_dump())


if __name__ == "__main__":
    main()
