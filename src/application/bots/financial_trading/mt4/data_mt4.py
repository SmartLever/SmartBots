import datetime as dt
import pandas as pd
from src.domain.models.trading.bar import Bar
from src.domain.models.trading.tick import Tick
from src.domain.models.trading.timer import Timer
from src.infraestructure.brokerMQ import Emit_Events
from src.application.services.health_handler import Health_Handler
import pytz
from src.application.base_logger import logger
from src.application import conf
from src.infraestructure.mt4.mt4_handler import Trading
from typing import Dict


class ProviderMT4(object):
    """
    Class
    for provider mt4.

    """

    def __init__(self, config_brokermq: Dict = {}, symbols=['EURUSD'], exchange_or_broker='darwinex'):
        self.config_brokermq = config_brokermq
        self.config_broker = {'MT4_HOST': conf.MT4_HOST, 'CLIENT_IF': conf.CLIENT_IF, 'PUSH_PORT': conf.PUSH_PORT,
                              'PULL_PORT_PROVIDER': conf.PULL_PORT_PROVIDER,
                              'SUB_PORT_PROVIDER': conf.SUB_PORT_PROVIDER}
        self.trading = Trading(exchange_or_broker=f'{exchange_or_broker}_provider', config_broker=self.config_broker,
                               config_brokermq=self.config_brokermq)
        self.health_handler = Health_Handler(n_check=10,
                                             name_service='data_realtime_provider_mt4',
                                             config=self.config_brokermq)
        self.emit = Emit_Events(config=config_brokermq)
        self.last_bar = {s: None for s in symbols}
        self.save_data = {symbol: [] for symbol in symbols}
        self.symbols = symbols

    def save_tick_data(self, msg=dict) -> None:
        """ Save tick data in dictionary """
        self.save_data[msg['Symbol']].append(msg)

    def create_tick_closed_day(self):
        for t in self.last_bar.values():
            tick = Tick(event_type='tick', tick_type='close_day', price=t.close,
                        ticker=t.ticker, datetime=t.datetime)
            print(f'tick close_day {tick.ticker} {tick.datetime} {tick.price}')
            self.emit.publish_event('tick', tick)

    """ Create thread for bar event """

    def create_bar(self, interval: str = '1min', verbose: bool = True):
        for symbol in self.save_data.keys():
            try:
                data = pd.DataFrame(self.save_data[symbol])
                data['Bid'] = data['Bid'].astype(float)
                data['Ask'] = data['Ask'].astype(float)
                data['price'] = (data['Bid'] + data['Ask']) / 2
            except Exception as e:
                data = []
                logger.error(f'* Error converting data to Dataframe: {e}')
            finally:
                self.save_data[symbol] = []  # clear data
            if len(data) > 0:
                data.index = pd.to_datetime(data['Time'], format='%Y-%m-%d %H:%M:%S.%f')
                ohlc = data['price'].astype(float).resample(interval).ohlc()
                # there are two bars and 2 dates
                if len(ohlc) > 1:
                    ohlc = ohlc[ohlc.index == ohlc.index.min()]

                ohlc['volume'] = float(0)
                dtime = dt.datetime(ohlc.index[0].year, ohlc.index[0].month, ohlc.index[0].day,
                                    ohlc.index[0].hour, ohlc.index[0].minute, ohlc.index[0].second, 0, pytz.UTC)
                bar = Bar(ticker=symbol, datetime=dtime, dtime_zone='UTC',
                          open=ohlc.open[0], bid=data['Bid'].values[-1], ask=data['Ask'].values[-1],
                          high=ohlc.high[0], low=ohlc.low[0], close=ohlc.close[0],
                          volume=ohlc.volume[0], exchange='mt4', provider='mt4', freq=interval)

                if verbose:
                    print(f'bar {bar.ticker} {bar.datetime} {bar.close}')
                self.emit.publish_event('bar', bar)
                self.last_bar[symbol] = bar
                self.health_handler.check()

    def create_timer(self):
        timer = Timer(datetime=dt.datetime.utcnow())
        print(timer)
        self.emit.publish_event('timer', timer)

    def get_stream_quotes_changes(self):
        self.trading.get_stream_quotes_changes(self.symbols, self.save_tick_data)