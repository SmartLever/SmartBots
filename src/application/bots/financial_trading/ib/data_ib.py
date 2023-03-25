import datetime as dt
import pandas as pd
from src.domain.models.trading.bar import Bar
from src.domain.models.trading.tick import Tick
from src.domain.models.trading.timer import Timer
from src.infrastructure.brokerMQ import Emit_Events
from src.application.services.health_handler import Health_Handler
import pytz
from src.application.base_logger import logger
from src.application import conf
from src.infrastructure.ib.ib_handler import Trading
from typing import Dict
import os

class ProviderIB(object):
    """
    Class
    for provider mt4.

    """

    def __init__(self, config_brokermq: Dict = {}, symbols=['EURUSD'], exchange_or_broker='ib'):
        self.config_brokermq = config_brokermq
        self.config_broker = {'HOST_IB': conf.HOST_IB, 'PORT_IB': int(conf.PORT_IB), 'CLIENT_IB': int(conf.CLIENT_IB_PROVIDER)}
        path_ticker = os.path.join(conf.path_to_principal, 'ticker_info_ib.csv')
        self.trading = Trading(exchange_or_broker=f'{exchange_or_broker}_provider', config_broker=self.config_broker,
                               config_brokermq=self.config_brokermq, path_ticker=path_ticker)
        self.health_handler = Health_Handler(n_check=10,
                                             name_service='data_realtime_provider_ib',
                                             config=self.config_brokermq)
        self.emit = Emit_Events(config=config_brokermq)
        self.last_bar = {s: None for s in symbols}
        self.save_data = {symbol: [] for symbol in symbols}
        self.symbols = symbols
        self.ticker_info = pd.read_csv(path_ticker, encoding="utf-8", sep=",")

    def save_tick_data(self, tickers) -> None:
        """ Save tick data in dictionary """
        for ticker in tickers:
            info_contract = ticker.contract.dict()
            info_contract_month = info_contract['lastTradeDateOrContractMonth']
            if info_contract_month != '':
                _symbol = info_contract['symbol']
                local_symbol = info_contract['localSymbol']
                symbol = f'{_symbol}{local_symbol[-2:-1]}{info_contract_month[2:-4]}'
            else:
                sec_type = info_contract['secType']
                if sec_type == 'CASH':
                    local_symbol = info_contract['localSymbol']
                    symbol = local_symbol.replace('.','')
                else:
                    symbol = info_contract['localSymbol']
            self.save_data[symbol].append(ticker.dict())

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
                data['Bid'] = data['bid'].astype(float)
                data['Ask'] = data['ask'].astype(float)
                data['price'] = (data['Bid'] + data['Ask']) / 2
            except Exception as e:
                data = []
                logger.error(f'* Error converting data to Dataframe: {e}')
            finally:
                self.save_data[symbol] = []  # clear data
            if len(data) > 0:
                data.index = pd.to_datetime(data['time'], format='%Y-%m-%d %H:%M:%S.%f')
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
                          volume=ohlc.volume[0], exchange='ib', provider='ib', freq=interval)

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