from dataclasses import dataclass, field
import pendulum
from pendulum import DateTime
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class OAuthResponse:
    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int
    scope: str
    kdnr: str
    bpid: str
    kontaktId: int

    @property
    def bearer_access_token(self):
        """Return the `Bearer` prefixed access token without double-prefixing."""
        prefix = "Bearer "
        if self.access_token.startswith(prefix):
            return self.access_token

        return f"{prefix}{self.access_token}"


@dataclass
class AccessToken(OAuthResponse):
    expires_at: DateTime = field(init=False)

    def __post_init__(self):
        """Calculate the UTC expiry time once, up front"""
        self.expires_at = pendulum.now("UTC").add(seconds=self.expires_in)

    def needs_refresh(self, buffer_seconds: int = 100) -> bool:
        """
        True if token is within `buffer_seconds` of expiry.
        Helps refresh the token early.
        """
        return pendulum.now("UTC") >= self.expires_at.subtract(seconds=buffer_seconds)


class APIConfig(BaseSettings):
    base_url: AnyHttpUrl = AnyHttpUrl("https://api.comdirect.de")
    client_id: str
    client_secret: str
    username: str
    password: str

    model_config = SettingsConfigDict(env_prefix="COMDIRECT_")
