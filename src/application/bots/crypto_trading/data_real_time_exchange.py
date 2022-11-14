""" Data provider all crypto exchange.
    Follow https://github.com/ccxt/ccxt
"""
from src.infrastructure.crypto.exchange_model import Trading
import datetime as dt
import pandas as pd
from src.domain.events import Bar, Tick
import schedule
import time
import threading
from src.infrastructure.brokerMQ import Emit_Events
from src.infrastructure.health_handler import Health_Handler
import os
import pytz
from src.domain.base_logger import logger
from src.application import conf


def get_thread_for_create_bar(interval: str = '1m', verbose: bool = True) -> threading.Thread:
    def create_tick_closed_day():
        for t in last_bar.values():
            tick = Tick(event_type='tick', tick_type='close_day', price=t.close,
                        ticker=t.ticker, datetime=t.datetime)
            print(f'tick close_day {tick.ticker} {tick.datetime} {tick.price}')
            logger.info(f'tick close_day {tick.ticker} {tick.datetime} {tick.price}')
            emit.publish_event('tick', tick)

    """ Create thread for bar event """
    def create_bar():
        bars_info = trading.get_historical_data(timeframe=interval, symbols=setting['symbols'],limit=2)
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
            emit.publish_event('bar', bar)
            last_bar[symbol] = bar
            health_handler.check()

    # Start publishing events in MQ
    emit = Emit_Events(config=config_brokermq)
    #
    health_handler = Health_Handler(n_check=10,
                                    name_service=os.path.basename(__file__).split('.')[0],
                                    config=config_brokermq)
    create_bar()
    # create scheduler for bar event
    schedule.every().minute.at(":00").do(create_bar)
    # create scheduler for close_day event
    schedule.every().day.at("00:00").do(create_tick_closed_day)



    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    global trading, setting, last_bar, config_brokermq
    exchange = conf.BROKER_CRYPTO
    config_brokermq = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
                       'password': conf.RABBITMQ_PASSWORD}
    print(f'* Starting {exchange} provider at {dt.datetime.utcnow()}')
    logger.info(f'* Starting {exchange} provider at {dt.datetime.utcnow()}')
    trading = Trading(exchange_or_broker=exchange, config_brokermq=config_brokermq)
    symbols = ['BTC-USDT', 'ETH-USDT']
    setting = {'symbols': symbols}
    last_bar = {s: None for s in symbols}
    get_thread_for_create_bar()
    x = threading.Thread(target=get_thread_for_create_bar)
    x.start()

