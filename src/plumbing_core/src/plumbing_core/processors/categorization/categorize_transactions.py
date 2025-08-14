import logging
import logfire

from typing import Dict, Any, Optional
from pydantic_ai import Agent

from .types import CategorizedBankTransaction


logger = logging.getLogger(__name__)


def categorize_transaction(
    agent: Agent, transaction: Dict[str, Any]
) -> Optional[CategorizedBankTransaction]:
    """Categorizes a transaction"""

    logfire.configure(
        send_to_logfire="if-token-present",  # only send to logfire if token is present in env
        service_name="plumbing-airflow",
    )
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)

    if not transaction:
        logger.info("No transaction passed, returning None")
        return None

    logger.info("Starting categorization of transaction")
    result = agent.run_sync(f"Transaction: '{transaction}'")
    logger.debug(f"Categorized transaction: '{result.output}'")

    logger.info("Finished categorization")
    return result
