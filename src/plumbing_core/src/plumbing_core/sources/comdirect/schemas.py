from typing import Dict

from .types import AccountBalance, AccountTransaction
from plumbing_core.shared import TIMESTAMP_FIELDS, get_sqlite_ddl_for_model


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
