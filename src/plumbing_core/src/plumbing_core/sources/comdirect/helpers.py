import uuid
import random
import logging
from httpx import URL, Client

from .types import APIConfig


logger = logging.getLogger(__name__)


def get_session_id() -> str:
    return str(uuid.uuid4())


def _get_request_id() -> str:
    nums = random.sample(range(0, 9), 9)
    nums = [str(num) for num in nums]
    return "".join(nums)


def get_client_request_id(session_id: str) -> dict[str, str]:
    return {"sessionId": session_id, "requestId": _get_request_id()}


def make_client(cfg: APIConfig) -> Client:
    return Client(
        base_url=str(cfg.base_url),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )


def get_request_url(base_url: URL | str, endpoint: str) -> str:
    url = str(base_url) + endpoint
    logger.debug(f"Returning request url: '{url}'")
    return url
