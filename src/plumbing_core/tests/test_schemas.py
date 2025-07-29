from plumbing_core.sources.comdirect.schemas import (
    get_sqlite_ddl_for_model,
    ACCOUNT_TRANSACTIONS_DDL,
    ACCOUNT_BALANCES_DDL,
    TIMESTAMP_FIELDS,
)
from plumbing_core.sources.comdirect.types import AccountTransaction, AccountBalance


class TestComdirectSchemas:
    """Test suite for Comdirect schema DDL generation"""

    def test_account_transaction_ddl_structure(self):
        """Test that AccountTransaction DDL is generated correctly without field duplication"""

        # Generate DDL for AccountTransaction model without extra fields
        base_ddl = get_sqlite_ddl_for_model(AccountTransaction)

        # Check that account_id appears in the base model
        assert "account_id" in base_ddl, (
            "account_id should be present in base AccountTransaction model"
        )

        # Count occurrences of account_id in the full DDL
        account_id_count = ACCOUNT_TRANSACTIONS_DDL.count("account_id")

        print(f"Full AccountTransaction DDL:\n{ACCOUNT_TRANSACTIONS_DDL}")
        print(f"account_id appears {account_id_count} times in DDL")

        # This should fail if there are duplicate account_id fields
        assert account_id_count == 1, (
            f"account_id should appear exactly once in DDL, but appears {account_id_count} times"
        )

    def test_account_transaction_model_fields(self):
        """Test that AccountTransaction model contains expected fields"""

        model_fields = list(AccountTransaction.model_fields.keys())

        # Verify account_id is already in the model
        assert "account_id" in model_fields, (
            "account_id should be a field in AccountTransaction model"
        )

        # Verify other expected fields
        expected_fields = [
            "reference",
            "booking_status",
            "booking_date",
            "amount__value",
            "amount__unit",
            "remittance_info",
            "transaction_type__key",
        ]

        for field in expected_fields:
            assert field in model_fields, (
                f"{field} should be present in AccountTransaction model"
            )

    def test_account_balance_ddl_structure(self):
        """Test that AccountBalance DDL is generated correctly (for comparison)"""

        base_ddl = get_sqlite_ddl_for_model(AccountBalance)

        # AccountBalance should naturally contain account_id without extra fields
        assert "account_id" in base_ddl, (
            "account_id should be present in AccountBalance model"
        )

        # Count occurrences in the full DDL
        account_id_count = ACCOUNT_BALANCES_DDL.count("account_id")

        print(f"Full AccountBalance DDL:\n{ACCOUNT_BALANCES_DDL}")
        print(f"account_id appears {account_id_count} times in AccountBalance DDL")

        assert account_id_count == 1, (
            "account_id should appear exactly once in AccountBalance DDL"
        )

    def test_timestamp_fields_in_ddl(self):
        """Test that timestamp fields are properly added to DDL"""

        # Check that timestamp fields are present in both DDLs
        for field_name in TIMESTAMP_FIELDS.keys():
            assert field_name in ACCOUNT_TRANSACTIONS_DDL, (
                f"{field_name} should be in AccountTransaction DDL"
            )
            assert field_name in ACCOUNT_BALANCES_DDL, (
                f"{field_name} should be in AccountBalance DDL"
            )

    def test_extra_fields_behavior(self):
        """Test how extra_fields parameter works with existing model fields"""

        # Test adding an extra field that doesn't exist in the model
        extra_ddl = get_sqlite_ddl_for_model(
            AccountTransaction, extra_fields={"new_field": "TEXT"}
        )

        assert "new_field" in extra_ddl, "Extra field should be added to DDL"

        # Test adding an extra field that already exists in the model
        # This demonstrates potential duplicate field issue that developers should avoid
        duplicate_ddl = get_sqlite_ddl_for_model(
            AccountTransaction,
            extra_fields={"account_id": "TEXT NOT NULL"},  # This field already exists!
        )

        account_id_count = duplicate_ddl.count("account_id")

        print(f"DDL with duplicate account_id:\n{duplicate_ddl}")

        # This shows that developers should not add fields via extra_fields that already exist in the model
        # The function doesn't prevent this, so it's the developer's responsibility
        assert account_id_count == 2, (
            "This demonstrates that duplicate fields can be created if not careful with extra_fields"
        )
