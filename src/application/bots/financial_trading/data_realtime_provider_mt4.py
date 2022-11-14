""" Data provider for MT4.
    recieve data from mt4 in ticks and create Bar for frequency.
    Send Events to RabbitMQ for further processing.
"""
import datetime as dt
import pandas as pd
from src.domain.events import Bar, Tick, Timer
import schedule
import time
import threading
from src.infrastructure.brokerMQ import Emit_Events
from src.infrastructure.health_handler import Health_Handler
import pytz
from src.domain.base_logger import logger
from src.application import conf
from src.infrastructure.mt4.mt4_model import Trading


def save_tick_data(msg=dict) -> None:
    """ Save tick data in dictionary """
    save_data[msg['Symbol']].append(msg)


def get_thread_for_create_bar(interval: str = '1min', verbose: bool = True) -> threading.Thread:
    def create_tick_closed_day():
        for t in last_bar.values():
            tick = Tick(event_type='tick', tick_type='close_day', price=t.close,
                        ticker=t.ticker, datetime=t.datetime)
            print(f'tick close_day {tick.ticker} {tick.datetime} {tick.price}')
            emit.publish_event('tick', tick)

    """ Create thread for bar event """
    def create_bar():
        for symbol in save_data.keys():
            try:
                data = pd.DataFrame(save_data[symbol])
                data['Bid'] = data['Bid'].astype(float)
                data['Ask'] = data['Ask'].astype(float)
                data['price'] = (data['Bid'] + data['Ask']) / 2
            except Exception as e:
                data = []
                logger.error(f'* Error converting data to Dataframe: {e}')
            finally:
                save_data[symbol] = []  # clear data
            if len(data) > 0:
                data.index = pd.to_datetime(data['Time'], format='%Y-%m-%d %H:%M:%S.%f')
                ohlc = data['price'].astype(float).resample(interval).ohlc()
                # there are two bars and 2 dates
                if len(ohlc) > 1:
                    ohlc = ohlc[ohlc.index == ohlc.index.min()]

                ohlc['volume'] = float(0)
                dtime = dt.datetime(ohlc.index[0].year, ohlc.index[0].month, ohlc.index[0].day,
                                    ohlc.index[0].hour, ohlc.index[0].minute, ohlc.index[0].second,0,pytz.UTC)
                bar = Bar(ticker=symbol, datetime=dtime, dtime_zone='UTC',
                          open=ohlc.open[0], bid=data['Bid'].values[-1], ask=data['Ask'].values[-1],
                          high=ohlc.high[0], low=ohlc.low[0], close=ohlc.close[0],
                          volume=ohlc.volume[0], exchange='mt4', provider='mt4', freq=interval)

                if verbose:
                    print(f'bar {bar.ticker} {bar.datetime} {bar.close}')
                emit.publish_event('bar', bar)
                last_bar[symbol] = bar
                health_handler.check()

    def create_timer():
        timer = Timer(datetime=dt.datetime.utcnow())
        print(timer)
        emit.publish_event('timer', timer)

    # create scheduler for bar event
    schedule.every().minute.at(":00").do(create_bar)
    # create scheduler for close_day event
    schedule.every().day.at("00:00").do(create_tick_closed_day)
    schedule.every().minute.at(":00").do(create_timer)
    # Start publishing events in MQ
    config_brokermq = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
                       'password': conf.RABBITMQ_PASSWORD}
    emit = Emit_Events(config=config_brokermq)
    #
    health_handler = Health_Handler(n_check=10,
                                    name_service='data_realtime_provider_mt4',
                                    config=config_brokermq)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    print(f'* Starting MT4 provider at {dt.datetime.utcnow()}')
    logger.info(f'Starting MT4 provider at {dt.datetime.utcnow()}')
    global save_data, last_bar, config_brokermq
    symbols = conf.FINANCIAL_SYMBOLS
    last_bar = {s: None for s in symbols}
    save_data = {symbol: [] for symbol in symbols}
    x = threading.Thread(target=get_thread_for_create_bar)
    x.start()
    setting = {'symbols': symbols}
    symbols = setting['symbols']
    config_broker = {'MT4_HOST': conf.MT4_HOST, 'CLIENT_IF': conf.CLIENT_IF, 'PUSH_PORT': conf.PUSH_PORT,
                     'PULL_PORT_PROVIDER': conf.PULL_PORT_PROVIDER, 'SUB_PORT_PROVIDER': conf.SUB_PORT_PROVIDER}
    trading = Trading(exchange_or_broker=f'{conf.BROKER_MT4_NAME}_provider', config_broker=config_broker)
    trading.get_stream_quotes_changes(symbols, save_tick_data)