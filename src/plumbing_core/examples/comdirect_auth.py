import logging

from plumbing_core.sources.comdirect import (
    APIConfig,
    get_session_id,
    authenticate_user_credentials,
)


def main() -> None:
    """Test the full auth flow reading the config from a .env file"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    cfg = APIConfig(_env_file=".env.comdirect")
    session_id = get_session_id()

    access_token = authenticate_user_credentials(cfg=cfg, session_id=session_id)

    print(access_token)


if __name__ == "__main__":
    main()
