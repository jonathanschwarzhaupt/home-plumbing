import json
import logging
import os

from cryptography.fernet import Fernet
from plumbing_core.sources.comdirect import (
    AccessToken,
    APIConfig,
    authenticate_user_credentials,
    get_session_id,
    refresh_token,
)

OP_ITEM_NAME = "comdirect-token"
UTF8 = "utf-8"


def load_token(file_path: str, fernet_key: Fernet) -> dict:
    with open(file_path, "rb") as f:
        encrypted = f.read()
    decrypted = fernet_key.decrypt(encrypted)
    return json.loads(decrypted.decode(UTF8))


def safe_token(file_path: str, fernet_key: Fernet, token: dict) -> None:
    encrypted = fernet_key.encrypt(json.dumps(token).encode(UTF8))
    with open(file_path, "wb") as f:
        f.write(encrypted)


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable: '{name}' is not set.")
    return value


def main() -> None:
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # If token not exist in 1password, copmlete comdirect oauth flow
    FERNET_KEY = Fernet(_require_env("FERNET_KEY"))
    TOKEN_FILE_PATH = _require_env("TOKEN_FILE_PATH")

    # parses comdirect required env vars
    cfg = APIConfig()

    try:
        token = AccessToken(**load_token(TOKEN_FILE_PATH, FERNET_KEY))
    except Exception:
        logging.info("Token not found. Entering comdirect oauth flow.")
        session_id = get_session_id()
        token = authenticate_user_credentials(cfg=cfg, session_id=session_id)
        if not token:
            raise RuntimeError("OAuth flow completed but returned no token.")

        # await create_op_item(client, vault_id, token.to_dict())
        safe_token(TOKEN_FILE_PATH, FERNET_KEY, token.to_dict())
        logging.info("Saved oauth credentials from comdirect, returning.")
        return

    logging.info("Token found. Checking if needs refresh.")
    if token.needs_refresh(buffer_seconds=240):
        logging.info("Token needs to be refreshed")
        new_token = refresh_token(cfg=cfg, token=token)
        if not new_token:
            raise RuntimeError("Token refresh returned None")

        logging.info(f"Token refreshed. Now expires at: {new_token.expires_at}")
        safe_token(TOKEN_FILE_PATH, FERNET_KEY, new_token.to_dict())
        return

    logging.info(f"Token does not need to be refreshed until {token.expires_at}")
    return


def run() -> None:
    main()


if __name__ == "__main__":
    main()
