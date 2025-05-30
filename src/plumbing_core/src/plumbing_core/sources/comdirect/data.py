import logging
import json
from typing import Literal
from datetime import date

from .types import APIConfig, AccountBalance, AccountTransaction
from .helpers import make_client, get_client_request_id, get_session_id, get_request_url


logger = logging.getLogger(__name__)


def get_accounts_balances(
    cfg: APIConfig, bearer_access_token: str
) -> list[AccountBalance]:
    """Gets the current balance for all accounts of the authenticated user"""
    logger.info("Starting to get account balances")

    if not bearer_access_token.startswith("Bearer "):
        logger.error("Invalid bearer access token")
        raise ValueError("`bearer_access_token` needs to start with 'Bearer '")

    # session id does not need to be the same as during auth process
    headers = {
        "Authorization": bearer_access_token,
        "x-http-request-info": json.dumps(
            {"clientRequestId": get_client_request_id(session_id=get_session_id())}
        ),
    }
    http_client = make_client(cfg=cfg)
    try:
        url = get_request_url(
            base_url=http_client.base_url,
            endpoint="api/banking/clients/user/v2/accounts/balances",
        )

        response = http_client.get(url=url, headers=headers)
        response.raise_for_status()

        logger.info(f"Obtained {len(response.json()['values'])} records from API")

    finally:
        http_client.close()

    result = [AccountBalance(**account) for account in response.json()["values"]]
    logger.info(f"Serialized {len(result)} records into `AccountBalance` objects")

    return result


def get_transaction_data_paginated(
    cfg: APIConfig,
    account_id: str,
    bearer_access_token: str,
    last_transaction_date: date,
    transaction_state: Literal["BOOKED", "NOTBOOKED", "BOTH"],
) -> list[AccountTransaction]:
    """Gets all transactions for a given account until a passed date"""
    accepted_states = ["BOOKED", "NOTBOOKED", "BOTH"]
    if transaction_state not in accepted_states:
        raise ValueError(f"`transaction_state` must be one of: '{accepted_states}'")

    pagination_index = 0
    logger.info("starting loop")
    result: list[AccountTransaction] = list()

    http_client = make_client(cfg=cfg)
    try:
        session_id = get_session_id()
        url = get_request_url(
            base_url=http_client.base_url,
            endpoint=f"api/banking/v1/accounts/{account_id}/transactions",
        )

        while True:
            headers = {
                "Authorization": bearer_access_token,
                "x-http-request-info": json.dumps(
                    {"clientRequestId": get_client_request_id(session_id=session_id)}
                ),
            }

            params = {
                "transactionState": transaction_state,
                "paging-first": pagination_index,
            }

            logger.debug(f"Params: '{params}'")

            response = http_client.get(
                url=url,
                params=params,
                headers=headers,
            )
            response.raise_for_status()

            logger.info(f"Obtained {len(response.json()['values'])} records from API")

            res = [
                AccountTransaction(**transaction)
                for transaction in response.json()["values"]
            ]
            logger.info(
                f"Serialized '{len(res)}' records into `AccountTransaction` objects"
            )
            result.extend(res)

            max_date = max(
                [
                    transaction.booking_date
                    for transaction in res
                    if transaction.booking_date
                ]
            )
            pagination_index += len(res)

            if max_date < last_transaction_date:
                logger.info("Finished")
                break

            logger.info(
                f"Last transaction date: {max_date} is not smaller than last transaction date: {last_transaction_date}. Continuing"
            )

    finally:
        http_client.close()
        logger.info(f"Returning {len(result)} transactions.")
        return result
