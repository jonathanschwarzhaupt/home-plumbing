import logging
from typing import Dict, Type, get_origin, get_args, Union, Optional
from pydantic import BaseModel
import pendulum

from .types import AccountBalance, AccountTransaction

logger = logging.getLogger(__name__)


def get_sqlite_ddl_for_model(
    model_class: Type[BaseModel], extra_fields: Optional[Dict[str, str]] = None
) -> str:
    """Generate SQLite CREATE TABLE DDL from Pydantic model with optional extra fields"""

    columns = []

    for field_name, field_info in model_class.model_fields.items():
        sqlite_type = _map_field_to_sqlite_type(field_info.annotation)

        # Determine if field is nullable
        is_nullable = not field_info.is_required() or _is_optional_type(
            field_info.annotation
        )

        column_def = f"{field_name} {sqlite_type}"
        if not is_nullable:
            column_def += " NOT NULL"

        columns.append(column_def)

    # Add extra fields if provided
    if extra_fields:
        for field_name, field_type in extra_fields.items():
            columns.append(f"{field_name} {field_type}")

    ddl = "(\n    " + ",\n    ".join(columns) + "\n)"
    logger.debug(f"Generated DDL for {model_class.__name__}: {ddl}")

    return ddl


def _map_field_to_sqlite_type(field_type) -> str:
    """Map Pydantic field type to SQLite type"""

    # Handle Optional/Union types - extract the non-None type
    if _is_optional_type(field_type):
        # For Optional[T], get the T part
        args = get_args(field_type)
        if args:
            field_type = args[0] if args[1] is type(None) else args[1]

    # Core type mappings - check against type objects, not instances
    if isinstance(field_type, str):
        return "TEXT"
    elif isinstance(field_type, int):
        return "INTEGER"
    elif isinstance(field_type, float):
        return "REAL"
    elif isinstance(field_type, bool):
        return "INTEGER"  # SQLite stores booleans as 0/1
    elif isinstance(field_type, pendulum.Date):
        return "TEXT"  # Store dates as ISO format strings
    elif isinstance(field_type, pendulum.DateTime):
        return "TEXT"  # Store datetimes as ISO format strings
    else:
        # Default fallback for complex types (store as JSON)
        logger.debug(f"Unknown field type {field_type}, defaulting to TEXT")
        return "TEXT"


def _is_optional_type(field_type) -> bool:
    """Check if a type is Optional (Union with None)"""
    origin = get_origin(field_type)
    if origin is Union:
        args = get_args(field_type)
        return len(args) == 2 and type(None) in args
    return False


# Standard timestamp fields for all Comdirect tables
TIMESTAMP_FIELDS = {
    "_inserted_at_day": "TEXT DEFAULT (date('now'))",
    "_inserted_at_ts": "TEXT DEFAULT CURRENT_TIMESTAMP",
}

# Pre-computed DDL constants for the three main tables with timestamp fields
ACCOUNT_BALANCES_DDL = get_sqlite_ddl_for_model(
    AccountBalance, extra_fields=TIMESTAMP_FIELDS
)
ACCOUNT_TRANSACTIONS_DDL = get_sqlite_ddl_for_model(
    AccountTransaction, extra_fields=TIMESTAMP_FIELDS
)

# Schema registry for easy lookup by table name
COMDIRECT_SCHEMAS: Dict[str, str] = {
    "account_balances": ACCOUNT_BALANCES_DDL,
    "account_transactions__booked": ACCOUNT_TRANSACTIONS_DDL,
    "account_transactions__not_booked": ACCOUNT_TRANSACTIONS_DDL,
}
