import datetime as dt
import pandas as pd
from src.domain.models.trading.bar import Bar
from src.domain.models.trading.tick import Tick
from src.infrastructure.brokerMQ import Emit_Events
from src.application.services.health_handler import Health_Handler
import pytz
from src.application.base_logger import logger
from src.infrastructure.crypto.exchange_handler import Trading
from typing import Dict


class ProviderCCXT(object):
    """
    Class
    for provider ccxt.

    """

    def __init__(self, config_brokermq: Dict = {}, symbols=['EURUSD'], exchange_or_broker='darwinex'):
        self.config_brokermq = config_brokermq
        self.trading = Trading(exchange_or_broker=exchange_or_broker, config_brokermq=config_brokermq)
        self.health_handler = Health_Handler(n_check=10,
                                             name_service=f'Provider {exchange_or_broker}',
                                             config=config_brokermq)
        self.emit = Emit_Events(config=config_brokermq)
        self.last_bar = {s: None for s in symbols}
        self.save_data = {symbol: [] for symbol in symbols}
        self.symbols = symbols

    def create_tick_closed_day(self):
        for t in self.last_bar.values():
            tick = Tick(event_type='tick', tick_type='close_day', price=t.close,
                        ticker=t.ticker, datetime=t.datetime)
            print(f'tick close_day {tick.ticker} {tick.datetime} {tick.price}')
            logger.info(f'tick close_day {tick.ticker} {tick.datetime} {tick.price}')
            self.emit.publish_event('tick', tick)

    """ Create thread for bar event """
    def create_bar(self, interval: str = '1m', verbose: bool = True):
        bars_info = self.trading.get_historical_data(timeframe=interval, symbols=self.symbols, limit=2)
        for b in bars_info:
            symbol = b['symbol']
            exchange = b['exchange']
            ohlc = b['candle']
            t = pd.to_datetime(ohlc[0] / 1000, unit='s')
            dtime = dt.datetime(t.year, t.month, t.day,
                                t.hour, t.minute, t.second,0, pytz.UTC)
            bar = Bar(ticker=symbol, datetime=dtime, dtime_zone='UTC',
                      open=ohlc[1],
                      high=ohlc[2], low=ohlc[3], close=ohlc[4],
                      volume=ohlc[5], exchange=exchange, provider=exchange, freq=interval)
            if verbose:
                print(f'bar {bar.ticker} {bar.datetime} {bar.close}')
            self.emit.publish_event('bar', bar)
            self.last_bar[symbol] = bar
            self.health_handler.check()
