from plumbing_core.sources.comdirect import (
    APIConfig,
    authenticate_user_credentials,
    get_session_id,
    AccessToken,
)


def main() -> None:
    """Script for testing"""

    cfg = APIConfig(_env_file=".env")
    session_id = get_session_id()

    access_token: AccessToken = authenticate_user_credentials(
        cfg=cfg, session_id=session_id
    )
    print(access_token)


if __name__ == "__main__":
    main()
