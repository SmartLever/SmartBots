""" Data provider for Kucoin.
    recieve data from kucoin websocket in ticks and create Bar for frequency.
    Send Events to RabbitMQ for further processing.
"""
import logging
from smartbots.crypto.kucoin_model import get_historical_data, get_realtime_data
import datetime as dt
import pandas as pd
from smartbots.events import Bar
import schedule
import time
import threading
from smartbots.decorators import log_start_end
from smartbots.brokerMQ import Emit_Events
from smartbots.health_handler import Health_Handler
import os
import pytz

logger = logging.getLogger(__name__)


async def save_tick_data(msg=dict) -> None:
    """ Save tick data in dictionary """
    save_data[msg['topic'].split(':')[-1]].append(msg['data'])


@log_start_end(log=logger)
def get_thread_for_create_bar(interval: str = '1min', verbose: bool = True) -> threading.Thread:
    """ Create thread for bar event """
    def create_bar():
        for symbol in save_data.keys():
            try:
                data = pd.DataFrame(save_data[symbol])
            except Exception as e:
                data = []
                print(e)
            finally:
                save_data[symbol] = []  # clear data
            if len(data) > 0:
                data.index = pd.to_datetime(data['time'] / 1000, unit='s')
                ohlc = data['price'].astype(float).resample(interval).ohlc()
                if len(ohlc) > 1:
                    ohlc = ohlc[ohlc.index == ohlc.index.max()]
                ohlc['volume'] = data['size'].astype(float).sum()  # sum volume
                dtime = dt.datetime(ohlc.index[0].year, ohlc.index[0].month, ohlc.index[0].day,
                                    ohlc.index[0].hour, ohlc.index[0].minute, ohlc.index[0].second,0,pytz.UTC)
                bar = Bar(ticker=symbol, datetime=dtime, dtime_zone='UTC',
                          open=ohlc.open[0],
                          high=ohlc.high[0], low=ohlc.low[0], close=ohlc.close[0],
                          volume=ohlc.volume[0], exchange='kucoin', provider='kucoin', freq=interval)
                if verbose:
                    print(bar)
                emit.publish_event('bar', bar)
                health_handler.check()


    # create scheduler
    schedule.every().minute.at(":00").do(create_bar)
    # Start publishing events in MQ
    emit = Emit_Events()
    #
    health_handler = Health_Handler(n_check=10,
                                    name_service=os.path.basename(__file__))

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    print(f'* Starting kucoin provider at {dt.datetime.utcnow()}')
    global save_data
    symbols = ['BTC-USDT', 'ETH-USDT']
    save_data = {symbol: [] for symbol in symbols}
    x = threading.Thread(target=get_thread_for_create_bar)
    x.start()
    setting = {'symbols': symbols}
    get_realtime_data(setting, save_tick_data)
