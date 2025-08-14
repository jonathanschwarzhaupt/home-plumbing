import logging

from typing import Dict, Any, Optional
from pydantic_ai import Agent

from .types import CategorizedBankTransaction


logger = logging.getLogger(__name__)


def categorize_transaction(
    agent: Agent, transaction: Dict[str, Any]
) -> Optional[CategorizedBankTransaction]:
    """Categorizes a transaction"""

    if not transaction:
        logger.info("No transaction passed, returning None")
        return None

    result = agent.run_sync(f"Transaction: '{transaction}'")

    logger.info("Finished categorization")
    return result.output
