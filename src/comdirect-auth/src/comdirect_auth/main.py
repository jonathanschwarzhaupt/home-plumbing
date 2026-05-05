import asyncio
import json
import logging
import os
from typing import Any, Dict

from onepassword import ItemCategory, ItemCreateParams, ItemField, ItemFieldType
from onepassword.client import Client
from plumbing_core.sources.comdirect import (
    AccessToken,
    APIConfig,
    authenticate_user_credentials,
    get_session_id,
    refresh_token,
)

OP_ITEM_NAME = "comdirect-token"


async def create_op_item(client, vault_id: str, value: Dict[str, Any] | None) -> str:
    """Creates a 1password item"""
    if not value:
        raise ValueError("value is None.")

    to_create = ItemCreateParams(
        title=OP_ITEM_NAME,
        category=ItemCategory.LOGIN,
        vaultId=vault_id,
        fields=[
            ItemField(
                id="password",
                title="password",
                fieldType=ItemFieldType.CONCEALED,
                value=json.dumps(value),
            ),
        ],
    )
    created_item = await client.items.create(to_create)
    logging.info(f"Created item '{created_item.title}' ({created_item.id})")
    return created_item.id


async def update_op_item(
    client, vault_id: str, item_id: str, value: Dict[str, Any]
) -> None:
    """Updates a 1password item"""
    item = await client.items.get(vault_id, item_id)

    item.fields[0].value = json.dumps(value)
    updated_item = await client.items.put(item)
    logging.info(f"Updated item: {updated_item.title} ({updated_item.id})")


async def find_item_id(client, vault_id: str, title: str) -> str | None:
    items = await client.items.list(vault_id)
    for item in items:
        if item.title == title:
            return item.id
    return None


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable: '{name}' is not set.")
    return value


async def main() -> None:
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # If token not exist in 1password, copmlete comdirect oauth flow
    token = _require_env("OP_SERVICE_ACCOUNT_TOKEN")
    vault_id = _require_env("OP_VAULT_ID")

    client = await Client.authenticate(
        auth=token, integration_name="Home Plumbing", integration_version="v1.0.0"
    )
    cfg = APIConfig()

    try:
        raw = await client.secrets.resolve(f"op://apps/{OP_ITEM_NAME}/password")
        token = AccessToken(**json.loads(raw))
    except Exception:
        logging.info("Token not found. Entering comdirect oauth flow.")
        session_id = get_session_id()
        token = authenticate_user_credentials(cfg=cfg, session_id=session_id)
        if not token:
            raise RuntimeError("OAuth flow completed but returned no token.")

        await create_op_item(client, vault_id, token.to_dict())
        logging.info("Saved oauth credentials from comdirect, returning.")
        return

    logging.info("Token found. Checking if needs refresh.")
    if token.needs_refresh():
        logging.info("Token needs to be refreshed")
        new_token = refresh_token(cfg=cfg, token=token)
        if not new_token:
            raise RuntimeError("Token refresh returned None")

        logging.info(f"Token refreshed. Now expires at: {new_token.expires_at}")
        item_id = await find_item_id(client, vault_id, OP_ITEM_NAME)
        if not item_id:
            raise ValueError(
                f"Could not find the ID of item in vault '{vault_id}' with title '{OP_ITEM_NAME}'"
            )
        await update_op_item(client, vault_id, item_id, new_token.to_dict())
        return

    logging.info(f"Token does not need to be refreshed until {token.expires_at}")
    return


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
