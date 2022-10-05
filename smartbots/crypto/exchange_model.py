""" DOCS: https://github.com/ccxt/ccxt/wiki/Manual#markets """


import dataclasses
import logging
from typing import Dict, List
import os
import sys
from asyncio import run, gather
import asyncio
import threading
from smartbots import conf
import time
import pandas as pd
import datetime as dt
from smartbots.brokerMQ import Emit_Events
from smartbots.decorators import log_start_end, check_api_key
import os
import ccxt

print('CCXT Version:', ccxt.__version__)

logger = logging.getLogger(__name__)


# default Callable
async def _callable(data: Dict) -> None:
    """Callback function for realtime data. [Source: Crypto Exchange]

    Parameters
    ----------
    data: Dict
        Realtime data.
    """
    print(data)


# Decorator for checking API key
def get_client(exchange: str = 'kucoin'):
    """Get Crypto Exchange client.

    Returns
    -------
    Client
        Crypto Exchange client.
    """
    if exchange == 'kucoin':
        client = ccxt.kucoin({'apiKey': conf.API_KUCOIN_API_KEYS,
                              'secret': conf.API_KUCOIN_API_SECRET,'enableRateLimit': True})
        return client
    else:
        return getattr(ccxt,exchange)({'enableRateLimit': True})


class Trading(object):
    """Class for trading on Kucoin.

    Attributes
    ----------
    client: Client
        Exchange client.
    """

    def __init__(self, send_orders_status: bool = True, name='kucoin') -> None:
        """Initialize class."""
        self.name = name
        self.client = get_client(exchange=name)
        # variables of status orders
        self.dict_open_orders = {}  # key is the order_id_sender, open order in the broker
        self.dict_cancel_and_close_orders = {}  # key is the order_id_sender, closed or cancelled order in the broker
        self.dict_from_strategies = {}  # key is order_id_sender from strategies, before send to broker or with error
        self.send_orders_status = send_orders_status
        if self.send_orders_status:
            self.emit_orders = Emit_Events()
        else:
            self.emit_orders = None

    def get_historical_data(self, timeframe :str ='1m', limit: int =2, start_date : dt.datetime =None,
                            end_date: dt.datetime= dt.datetime.utcnow(),
                            setting: dict = {'symbols': List[str]}) -> List[Dict]:
        """Return realtime data on freq for a list of symbols.
        Parameters
        ----------
        exchange: str (default: 'kucoin')
        timeframe: str (default: '1m')
        limit: int (default: 2, last ohlcv)
        since: from timestamp (default: None)
        setting: dict (default: {'symbols': List[str]})
            Symbols of the assets. Example: BTC-USDT, ETH-USDT, etc.
        """
        def get_ohlcv_last(symbol, timeframe):
            ohlcv = self.client.fetch_ohlcv(symbol, timeframe, None, 2)
            if len(ohlcv):
                first_candle = ohlcv[0]
                datetime = self.client.iso8601(first_candle[0])
                return {'datetime': datetime, 'exchange': self.client.id, 'symbol': symbol,
                                 'candle': first_candle}

        def get_ohlcv(symbol, timeframe, limit=1500,since=None):
            ohlcv = self.client.fetch_ohlcv(symbol, timeframe, since, limit)
            if len(ohlcv):
                return ohlcv

        symbols = setting['symbols']
        if type(symbols) is str:
            symbols = [symbols]
        bars = []
        if limit == 2: # last ohlcv
            for symbol in symbols:
                    try:
                        bars.append(get_ohlcv_last(symbol, timeframe))
                    except Exception as e:
                        print(type(e).__name__, str(e))
                        time.sleep(0.1)
                        bars.append(get_ohlcv_last(symbol, timeframe))
            return bars
        else: # historical data
            bars = {s: [] for s in symbols}
            for symbol in symbols:
                _to_date = self.client.parse8601(str(end_date))  # milliseconds
                _since = self.client.parse8601(str(start_date))
                keep_going = True
                while keep_going:
                    try:
                        _df = get_ohlcv(symbol, timeframe, limit=1500, since=_since)
                        if _df is not None:
                            df = pd.DataFrame(_df, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
                            df.index = pd.to_datetime(df['datetime'], unit='ms')
                            df['symbol'] = symbol
                            df['exchange'] = self.name
                            bars[symbol].append(df)
                            _since = _df[-1][0] + 60000 # 1 min
                            print(f'{symbol} Since: {self.client.iso8601(_since)}')
                            if _since >= _to_date:
                                keep_going = False
                    except Exception as e:
                        print(type(e).__name__, str(e))
                        time.sleep(1)

            return {s: pd.concat(bars[s]) for s in symbols}




