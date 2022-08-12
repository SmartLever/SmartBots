import dataclasses
import logging
from typing import Dict, List
from kucoin.client import Client
import asyncio
from smartbots import conf
import time
import pandas as pd
import datetime as dt
from smartbots.decorators import log_start_end, check_api_key
import os

logger = logging.getLogger(__name__)


# default Callable
async def _callable(data: Dict) -> None:
    """Callback function for realtime data. [Source: Betfair]

    Parameters
    ----------
    data: Dict
        Realtime data.
    """
    print(data)


# Decorator for checking API key
@check_api_key(
    [
        "API_BETFAIR_API_KEYS",
        "API_BETFAIR_API_SECRET",
        "API_BETFAIR_API_PASSPHRASE",
    ]
)
def get_client():
    """Get Betfair client.

    Returns
    -------
    Client
        Betfair client.
    """
    return Client()


class Trading(object):
    """Class for trading Betting on Betfair.

    Attributes
    ----------
    client: Client
        Betfair client.
    """

    def __init__(self):
        """Initialize class."""
        self.client = get_client()

    def send_order(self, order: dataclasses.dataclass) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        print(order)


@log_start_end(log=logger)
def get_realtime_data(Tickets: List[str], callback: callable = _callable) -> None:
    """Return realtime data for a list of tickers (Events). [Source: Betfair]

    Parameters
    ----------
    symbols: List[str]
        Symbols of the assets. Example: BTC-USDT, ETH-USDT, etc.
    callback: callable (data: Dict) -> None

    """