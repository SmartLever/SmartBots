import dataclasses
import logging
from typing import Dict, List
from kucoin.client import Client
import asyncio
from smartbots import conf
import time
import pandas as pd
import datetime as dt
from kucoin.asyncio import KucoinSocketManager
from smartbots.decorators import log_start_end, check_api_key
import os

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
    return Client(conf.API_KUCOIN_API_KEYS, conf.API_KUCOIN_API_SECRET, conf.API_KUCOIN_API_PASSPHRASE)


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
def get_historical_data(symbol: str, interval: str = '1day',
                        start_date: dt.datetime = dt.datetime(2020, 1, 1),
                        end_date: dt.datetime = dt.datetime.now()) -> pd.DataFrame:
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
    def _get_data_limit_1500():
        keep_going = True
        while keep_going:
            try:
                klines = client.get_kline_data(symbol, kline_type=interval, start=start, end=end)
                data = pd.DataFrame(klines)
                keep_going = False
            except Exception as e:
                if e.code == '429000':  # too many requests
                    print('Waiting for 10 seconds for limits of requests')
                    time.sleep(10)
                else:
                    keep_going = False
                    print(e)
        return data

    datas = []
    keep_going = True
    hist_data_path = os.path.join(conf.path_to_temp, 'historical_kucoin_' + symbol + '.csv')

    # check if historical data already exists
    if os.path.exists(hist_data_path):
        print('Historical data already exists in temp folder')
        data_hist = pd.read_csv(hist_data_path, index_col=[0]).sort_index(ascending=True)
        data_hist.index = pd.to_datetime(data_hist.index)
        end_date = data_hist.index.min().to_pydatetime()

    # Get historical data fresh, limit of 1500 rows, so create loop for solving this issue
    while keep_going:
        start = int(start_date.timestamp())
        end = int(end_date.timestamp())
        data = _get_data_limit_1500()
        if len(data) > 0 and end > start:
            data.columns = ['datetime', 'open', 'close', 'high', 'low', 'trasactions','volume'] # candle
            data['datetime'] = [dt.datetime.fromtimestamp(int(d)) for d in data['datetime'].values]
            data = data.set_index("datetime")
            data = data.sort_index(ascending=True)
            if len(datas) > 0:
                data = data[data.index < end_date]  # to avoid duplicates
            datas.append(data)
            end_date = data.index.min().to_pydatetime()
            print(end_date)
            time.sleep(1)
        else:
            keep_going = False
        if len(datas) > 20: # saving to csv as point of control
            if os.path.exists(hist_data_path):
                read_df = pd.read_csv(hist_data_path, index_col=[0]).sort_index(ascending=True)
                read_df.index = pd.to_datetime(read_df.index)
            else:
                read_df = pd.DataFrame()
            df = pd.concat(datas).sort_index(ascending=True)
            read_df = pd.concat([read_df, df]).sort_index(ascending=True)
            read_df.to_csv(hist_data_path, index=True)
            datas = [] # reinitialize

    # Check if exist file
    read_df = pd.DataFrame()
    if os.path.exists(hist_data_path):
        read_df = pd.read_csv(hist_data_path, index_col=[0]).sort_index(ascending=True)
        read_df.index = pd.to_datetime(read_df.index)
    if len(datas) > 0:
        df = pd.concat(datas) # add new data
        read_df = pd.concat([read_df, df]).sort_index(ascending=True)
    return read_df, hist_data_path


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
