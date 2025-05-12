import uuid
import random
from httpx import Client, URL

from .types import APIConfig


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


def get_request_url(base_url: URL, endpoint: str) -> str:
    return str(base_url) + endpoint
