import logging
from dataclasses import dataclass, field
from datetime import date
import pendulum
from pendulum import DateTime
from typing import Optional, Any, Dict
from pydantic import BaseModel, model_validator, field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


from .constants import ACCOUNT_BALANCE_FIELD_PATHS, ACCOUNT_TRANSACTION_FIELD_PATHS

logger = logging.getLogger(__name__)


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

    def to_dict(self) -> Dict[str, Any]:
        """Converts the `AccessToken` to a python dictionary"""
        expires_at_string = self.expires_at.to_datetime_string()
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "refresh_token": self.refresh_token,
            "expires_in": self.expires_in,
            "scope": self.scope,
            "kdnr": self.kdnr,
            "bpid": self.bpid,
            "kontaktId": self.kontaktId,
            "expires_at": expires_at_string,
        }


class APIConfig(BaseSettings):
    base_url: AnyHttpUrl = AnyHttpUrl("https://api.comdirect.de")
    client_id: str
    client_secret: str
    username: str
    password: str

    model_config = SettingsConfigDict(env_prefix="COMDIRECT_")


class AccountBalance(BaseModel):
    account_id: str
    account_display_id: int
    currency: str
    client_id: str
    account_type__key: str
    account_type__text: str
    iban: str
    bic: str
    credit_limit__value: float
    credit_limit__unit: str
    balance__value: float
    balance__unit: str
    balance_eur__value: float
    balance_eur__unit: str
    available_cash_amount__value: float
    available_cash_amount__unit: str
    available_cash_amount_eur__value: float
    available_cash_amount_eur__unit: str

    @model_validator(mode="before")
    def _flatten(cls, values):
        """This runs before before pydantic maps values to fields"""
        return _make_flat(values, ACCOUNT_BALANCE_FIELD_PATHS)


class AccountTransaction(BaseModel):
    reference: Optional[str]
    booking_status: str
    booking_date: Optional[date]
    amount__value: float
    amount__unit: str
    remitter__holder_name: Optional[str]
    deptor: Optional[str]
    creditor__holder_name: Optional[str]
    creditor__iban: Optional[str]
    creditor__bic: Optional[str]
    valuta_date: Optional[date]
    direct_debit_creditor_id: Optional[str]
    direct_debit_mandate_id: Optional[str]
    end_to_end_reference: Optional[str]
    new_transaction: bool
    remittance_info: str
    transaction_type__key: str
    transaction_type__text: str

    @field_validator("remittance_info", mode="after")
    def strip_whitespace(cls, v: str) -> str:
        """Remove whitespaces from field"""
        return " ".join(v.split())

    @field_validator("reference", mode="after")
    def whitespace_to_none(cls, v: str) -> Optional[str]:
        """Remove whitespaces from field"""
        if v and len(v.strip()) == 0:
            return None
        return v

    @model_validator(mode="before")
    def _flatten(cls, values):
        """This runs before before pydantic maps values to fields"""
        return _make_flat(values, ACCOUNT_TRANSACTION_FIELD_PATHS)


def _make_flat(
    acct: dict[str, Any], field_paths: dict[str, list[str]]
) -> dict[str, Any]:
    """Flattens a dictionary based on field paths to traverse"""

    return {
        field: _exctract_from_path(acct, path) for field, path in field_paths.items()
    }


def _exctract_from_path(data: dict[str, Any], path: list[str]) -> Any:
    """Walks a path"""

    err_value = None

    for p in path:
        try:
            data = data[p]
        except KeyError:
            logger.debug(
                f"Could not traverse path due to key error. Did not find '{p}' for '{path}' in data: '{data}'"
            )
            return err_value
        except TypeError:
            logger.debug(
                f"Could not traverse path due to value error. Found 'None' at '{p}' for '{path}' in data: '{data}'"
            )
            return err_value

    return data
