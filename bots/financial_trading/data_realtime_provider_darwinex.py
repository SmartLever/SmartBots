""" Data provider for Darwinex.
    recieve data from mt4 Darwinex in ticks and create Bar for frequency.
    Send Events to RabbitMQ for further processing.
"""
from smartbots.financial.darwinex_model import get_realtime_data
import datetime as dt
import pandas as pd
from smartbots.events import Bar, Tick, Timer
import schedule
import time
import threading
from smartbots.brokerMQ import Emit_Events
from smartbots.health_handler import Health_Handler
import pytz
from smartbots.base_logger import logger
from smartbots import conf

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
                          volume=ohlc.volume[0], exchange='mt4_darwinex', provider='mt4_darwinex', freq=interval)

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
    emit = Emit_Events()
    #
    health_handler = Health_Handler(n_check=10,
                                    name_service='data_realtime_provider_darwinex')

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    print(f'* Starting MT4 Darwinex provider at {dt.datetime.utcnow()}')
    logger.info(f'Starting MT4 Darwinex provider at {dt.datetime.utcnow()}')
    global save_data, last_bar
    symbols = conf.FINANCIAL_SYMBOLS
    last_bar = {s: None for s in symbols}
    save_data = {symbol: [] for symbol in symbols}
    x = threading.Thread(target=get_thread_for_create_bar)
    x.start()
    setting = {'symbols': symbols}
    get_realtime_data(setting, save_tick_data)
