import json
from time import sleep
from typing import Optional
from httpx import Client

from .types import AccessToken, OAuthResponse, APIConfig
from .helpers import get_request_url, get_client_request_id, make_client


def authenticate_user_credentials(
    cfg: APIConfig, session_id: str, wait_for_challenge_seconds: int = 20
) -> Optional[AccessToken]:
    """Completes the comdirect OAuth flow and returns an `AccessToken`."""

    http_client = make_client(cfg=cfg)
    try:
        o_auth_response = _generate_oauth_token(cfg=cfg, http_client=http_client)
        session_tan_id = _get_session_object(
            session_id=session_id,
            access_token=o_auth_response.bearer_access_token,
            client_id=o_auth_response.kontaktId,
            http_client=http_client,
        )

        challenge_id = _anlage_validierung_session_tan(
            session_id=session_id,
            access_token=o_auth_response.bearer_access_token,
            session_tan_id=session_tan_id,
            http_client=http_client,
        )

        sleep(wait_for_challenge_seconds)

        _mark_session(
            session_id=session_id,
            access_token=o_auth_response.bearer_access_token,
            session_tan_id=session_tan_id,
            challenge_id=challenge_id,
            http_client=http_client,
        )

        return _cd_secondary_flow(
            cfg=cfg, access_token=o_auth_response.access_token, http_client=http_client
        )
    finally:
        http_client.close()


def refresh_token(cfg: APIConfig, token: AccessToken) -> Optional[AccessToken]:
    """Refreshes an existing access token"""

    http_client = make_client(cfg=cfg)
    try:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": cfg.client_id,
            "client_secret": cfg.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
        }

        url = get_request_url(cfg.base_url, "oauth/token")
        response = http_client.post(url=url, data=data, headers=headers)
        response.raise_for_status()
        return AccessToken(**response.json())

    finally:
        http_client.close()


def _generate_oauth_token(cfg: APIConfig, http_client: Client) -> OAuthResponse:
    """First step of the OAuth flow: generate an OAuth token."""

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "grant_type": "password",
        "username": cfg.username,
        "password": cfg.password,
    }

    url = get_request_url(base_url=http_client.base_url, endpoint="oauth/token")
    response = http_client.post(url=url, data=data, headers=headers)
    response.raise_for_status()

    return OAuthResponse(**response.json())


def _get_session_object(
    session_id: str, access_token: str, client_id: int, http_client: Client
) -> str:
    """Second step of the OAuth flow: Get session object."""

    headers = {
        "Authorization": access_token,
        "x-http-request-info": json.dumps(
            {"clientRequestId": get_client_request_id(session_id=session_id)}
        ),
    }

    url = get_request_url(
        base_url=http_client.base_url,
        endpoint=f"api/session/clients/{client_id}/v1/sessions",
    )
    response = http_client.get(url=url, headers=headers)
    response.raise_for_status()

    return response.json()[0]["identifier"]


def _anlage_validierung_session_tan(
    session_id: str, access_token: str, session_tan_id: str, http_client: Client
) -> int:
    """Third step of the OAuth flow: Get tan object, which prompts a PhotoTan challenge for the user."""
    headers = {
        "Authorization": access_token,
        "x-http-request-info": json.dumps(
            {"clientRequestId": get_client_request_id(session_id=session_id)}
        ),
    }

    data = {
        "identifier": session_tan_id,
        "sessionTanActive": True,
        "activated2FA": True,
    }

    url = get_request_url(
        base_url=http_client.base_url,
        endpoint=f"api/session/clients/user/v1/sessions/{session_tan_id}/validate",
    )

    response = http_client.post(url=url, headers=headers, json=data)
    response.raise_for_status()

    return json.loads(response.headers["x-once-authentication-info"])["id"]


def _mark_session(
    session_id: str,
    access_token: str,
    session_tan_id: str,
    challenge_id: int,
    http_client: Client,
) -> None:
    """Fourth step of the OAuth flow: Mark tan challenge as active after user approved PhotoTan challenge."""

    headers = {
        "Authorization": access_token,
        "x-once-authentication-info": json.dumps({"id": challenge_id}),
        "x-http-request-info": json.dumps(
            {"clientRequestId": get_client_request_id(session_id=session_id)}
        ),
    }

    data = {
        "identifier": session_tan_id,
        "sessionTanActive": True,
        "activated2FA": True,
    }

    url = get_request_url(
        base_url=http_client.base_url,
        endpoint=f"api/session/clients/user/v1/sessions/{session_tan_id}",
    )

    response = http_client.patch(url=url, headers=headers, json=data)
    response.raise_for_status()


def _cd_secondary_flow(
    cfg: APIConfig, access_token: str, http_client: Client
) -> AccessToken:
    """Last step of the OAuth flow: Obtain access token."""

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "grant_type": "cd_secondary",
        "token": access_token,
    }

    url = get_request_url(base_url=http_client.base_url, endpoint="oauth/token")

    response = http_client.post(url=url, headers=headers, data=data)
    response.raise_for_status()

    return AccessToken(**response.json())
