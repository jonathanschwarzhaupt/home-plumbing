from typing import Literal
from pydantic import Field, BaseModel

from plumbing_core.shared import get_sqlite_ddl_for_model, TIMESTAMP_FIELDS


class CategorizedBankTransaction(BaseModel):
    """Bank transaction categorized"""

    account_id: str = Field(
        description="The ID of the account used to make the transaction"
    )
    reference: str = Field(description="The ID of the transaction itself")
    category: Literal[
        "Housing",
        "Household Items/Supplies",
        "Utilities",
        "Transportation",
        "Food",
        "Restaurant",
        "Clothing",
        "Medical/Healthcare",
        "Insurance",
        "Personal",
        "Savings",
        "Education",
        "Entertainment",
        "Gifts/Donations",
    ] = Field(description="The category of the transaction")
    summary: str = Field(
        description="A summary of the transaction used for first-glance details"
    )


CATEGORIZED_BANK_TRANSACTION_DDL = get_sqlite_ddl_for_model(
    CategorizedBankTransaction, extra_fields=TIMESTAMP_FIELDS
)
