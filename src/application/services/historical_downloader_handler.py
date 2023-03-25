""" Download historical data from Data Exchage and save it for use in the bot.
 Doc: https://github.com/man-group/arctic/wiki/Chunkstore

 """
import os
import datetime as dt
from typing import List
import pandas as pd
from src.domain.decorators import log_start_end
from src.application.services.historical_utils_handler import save_historical, read_historical, clean_symbol
from src.application import conf
from src.infrastructure.crypto.exchange_handler import Trading as Trading_Crypto
from src.infrastructure.mt4.mt4_handler import Trading as Trading_Darwinex
from src.infrastructure.ib.ib_handler import Trading as Trading_ib


def save_test_data():
    """ Save test data for testing purposes """
    path = os.path.join(conf.path_modulo, 'crypto', '../data/data_crypto')
    # check files in folder if pkl
    files = [f for f in os.listdir(path) if f.endswith('.pkl')]
    for file in files:
        df = pd.read_pickle(os.path.join(path, file), compression='gzip')
        save_historical(file.split('.')[0], df, name_library='test_historical_1min')


def historical_downloader(symbols: List[str] = ["EURUSD"], start_date: dt.datetime = dt.datetime(2022, 7, 1),
                          end_date: dt.datetime = dt.datetime.utcnow(),
                          interval: str = '1m', provider: str = 'darwinex', clean_symbols_database: list = [],
                          unit=''):
    """ Main function """
    name_library = f'{provider}_historical_{interval}'
    # Connect to the exchange or broker
    if provider == 'darwinex':
        config_broker = {'DWT_FTP_USER': conf.DWT_FTP_USER, 'DWT_FTP_PASS': conf.DWT_FTP_PASS,
                         'DWT_FTP_HOSTNAME': conf.DWT_FTP_HOSTNAME, 'DWT_FTP_PORT': conf.DWT_FTP_PORT,
                         'MT4_HOST': conf.MT4_HOST, 'CLIENT_IF': conf.CLIENT_IF, 'PUSH_PORT': conf.PUSH_PORT,
                         'PULL_PORT_BROKER': conf.PULL_PORT_BROKER, 'SUB_PORT_BROKER': conf.SUB_PORT_BROKER
                         }
        trading = Trading_Darwinex(send_orders_status=False, config_broker=config_broker)
    elif provider == 'ib':
        config_broker = {'HOST_IB': conf.HOST_IB, 'PORT_IB': int(conf.PORT_IB),
                         'CLIENT_IB': 99}
        path_ticker = os.path.join(conf.path_to_principal, 'ticker_info_ib.csv')
        trading = Trading_ib(send_orders_status=False, exchange_or_broker=f'{provider}_broker',
                             config_broker=config_broker,
                             path_ticker=path_ticker)
    else:
        trading = Trading_Crypto(exchange_or_broker=provider)

    # check if symbols por cleaning
    if len(clean_symbols_database) > 0:
        clean_symbol(clean_symbols_database, name_library)

    # Get historical data
    for symbol in symbols:
        # Check if exist data in DB
        data_last = read_historical(symbol, name_library, last_month=True)
        # if exist data in DB, check if data is complete for the query period
        if len(data_last) > 0:  # if exist data in DB, do smart update
            start_date = data_last.index.max() + dt.timedelta(minutes=1)
            start_date = start_date.to_pydatetime()
        # load from provider
        if provider == 'ib':
            data = trading.get_historical_data(timeframe=interval, start_date=start_date,
                                               end_date=end_date, symbols=symbol, unit=unit)
        else:
            data = trading.get_historical_data(timeframe=interval, limit=1500, start_date=start_date,
                                               end_date=end_date, symbols=[symbol])[symbol]

        # change types to float for columns with numeric values (in this case all columns)
        for c in data.columns:
            if c not in ['symbol', 'datetime', 'exchange', 'ticker', 'dtime_zone', 'provider', 'freq']:
                data[c] = data[c].astype(float)

        if len(data) > 0 and len(data_last) > 0:  #
            # update data
            data = data[data.index > data_last.index.max()]
            data = pd.concat([data_last, data])

        if len(data) > 0:  # save data
            save_historical(symbol, data, name_library=name_library)
        print(f'* Historical data for {symbol} saved')


if __name__ == '__main__':
    # test
    provider = 'ib'  # ib, darwinex
    interval = '1'  # darwinex: 1m , ib : 1
    unit = 'hour'  # just for ib: hour, min, day
    symbols = ['AUDNZD']  # List of symbols to download from provider
    start_date = dt.datetime(2023, 2, 1)  # Start date of data to download
    end_date = dt.datetime.utcnow()  # End date of data to download
    # Interval of data to download,
    historical_downloader(symbols=symbols, start_date=start_date, end_date=dt.datetime.utcnow(),
                          provider=provider, interval=interval, unit=unit)


