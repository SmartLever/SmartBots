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

logger = logging.getLogger(__name__)


async def save_tick_data(msg=dict) -> None:
    """ Save tick data in dictionary """
    save_data[msg['topic'].split(':')[-1]].append(msg['data'])


@log_start_end(log=logger)
def get_thread_for_create_bar(interval: str = '1min', verbose: bool = True) -> threading.Thread:
    """ Create thread for bar event """

    def create_bar():
        for symbol in save_data.keys():
            data = pd.DataFrame(save_data[symbol])
            save_data[symbol] = []  # clear data
            if len(data) > 0:
                data.index = pd.to_datetime(data['time'] / 1000, unit='s')
                ohlc = data['price'].astype(float).resample(interval).ohlc()
                if len(ohlc) > 1:
                    ohlc = ohlc[ohlc.index == ohlc.index.max()]
                ohlc['volume'] = data['size'].astype(float).sum() # sum volume
                dtime = dt.datetime(ohlc.index[0].year, ohlc.index[0].month, ohlc.index[0].day,
                                    ohlc.index[0].hour, ohlc.index[0].minute, ohlc.index[0].second)
                bar = Bar(ticker=symbol, datetime=dtime, dtime_zone='UTC', datetime_epoch =dtime.timestamp(),
                          open=ohlc.open[0],
                          high=ohlc.high[0], low=ohlc.low[0], close=ohlc.close[0],
                          volume=ohlc.volume[0],exchange= 'kucoin', provider= 'kucoin', freq=interval)
                if verbose:
                    print(bar)
                emit.publish_event('bar', bar)

    # create scheduler
    schedule.every().minute.at(":00").do(create_bar)
    # Start publishing events in MQ
    emit = Emit_Events()

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
    get_realtime_data(symbols, save_tick_data)
