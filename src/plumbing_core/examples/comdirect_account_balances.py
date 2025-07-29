import logging
from pathlib import Path

from plumbing_core.sources.comdirect import (
    AccountBalance,
    APIConfig,
    authenticate_user_credentials,
    get_accounts_balances,
    get_session_id,
    COMDIRECT_SCHEMAS,
)

from plumbing_core.destinations.turso import TursoConfig, write_account_balances


def main() -> None:
    """Test the full auth flow and print all account balances reading the config from a .env file"""
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

    logging.info("Loading to Turso sqlite")
    db_path = Path.cwd() / "comdirect_turso.db"

    # Local only:
    # db_config = TursoConfig(db_path=db_path)

    # Use remote
    db_config = TursoConfig(db_path=db_path, _env_file=".env.turso")

    record_count = write_account_balances(
        balances=account_balances,
        config=db_config,
        ddl=COMDIRECT_SCHEMAS["account_balances"],
    )
    logging.info(f"Loaded {record_count} records")


if __name__ == "__main__":
    main()
