import dataclasses
import logging
from typing import Dict, List
from kucoin.client import Client
import asyncio
from smartbots import conf
import pandas as pd
import datetime as dt
from kucoin.asyncio import KucoinSocketManager
from smartbots.decorators import log_start_end, check_api_key


logger = logging.getLogger(__name__)

# default Callable
async def _callable(data: Dict) -> None:
    """Callback function for realtime data. [Source: Kucoin]

    Parameters
    ----------
    data: Dict
        Realtime data.
    """
    print(data)


# Decorator for checking API key
@check_api_key(
    [
         "API_KUCOIN_API_KEYS",
         "API_KUCOIN_API_SECRET",
         "API_KUCOIN_API_PASSPHRASE",
     ]
 )
def get_client():
    """Get Kucoin client.

    Returns
    -------
    Client
        Kucoin client.
    """
    return Client(conf.API_KUCOIN_API_KEYS, conf.API_KUCOIN_API_SECRET,conf.API_KUCOIN_API_PASSPHRASE)


class Trading(object):
    """Class for trading on Kucoin.

    Attributes
    ----------
    client: Client
        Kucoin client.
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
def get_historical_data(symbol: str, interval: str='1day',
                        start_date: dt.datetime = dt.datetime(2020,1,1),
                        end_date: dt.datetime  =dt.datetime.now()) -> pd.DataFrame:
    """Return historical data for a given symbol. [Source: Kucoin]

    Parameters
    ----------
    symbol: str
        Symbol of the asset. Example: BTC-USDT, ETH-USDT, etc.
    interval: str
        Interval of the data.
    start_date: dt.datetime
        Start date of the data.
    end_date: dt.datetime
        End date of the data.

    Returns
    ----------
    data : pd.DataFrame
        Historical data for the given symbol.
    """
    client = get_client()

    # In timestamp format
    start = int(start_date.timestamp())
    end = int(end_date.timestamp())

    klines = client.get_kline_data(symbol, kline_type=interval, start=start, end=end)
    data = pd.DataFrame(klines)
    data.columns = ['datetime', 'open', 'close', 'high', 'low', 'transactions', 'volume']
    data['datetime'] = [dt.datetime.fromtimestamp(int(d)) for d in data['datetime'].values]
    data = data.set_index("datetime")
    data = data.sort_index()
    return data

@log_start_end(log=logger)
def get_realtime_data(symbols: List[str], callback: callable = _callable) -> None:
    """Return realtime data for a list of symbols. [Source: Kucoin]

    Parameters
    ----------
    symbols: List[str]
        Symbols of the assets. Example: BTC-USDT, ETH-USDT, etc.
    callback: callable (data: Dict) -> None

    """
    async def main():
        ksm = await KucoinSocketManager.create(loop, client, callback)
        # subscribe to all symbols  (this is the default)
        for symbol in symbols:
            await ksm.subscribe('/market/ticker:' + symbol)

        while True:
            await asyncio.sleep(20, loop=loop)

    if type(symbols) is str:
        symbols = [symbols]

    client = get_client()

    global loop
    # run the loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

