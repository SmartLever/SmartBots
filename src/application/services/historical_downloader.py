""" Download historical data from Data Exchage and save it for use in the bot.
 Doc: https://github.com/man-group/arctic/wiki/Chunkstore

 """
import logging
import os
import datetime as dt
from typing import List
import pandas as pd
from src.domain.decorators import log_start_end
from src.application.services.historical_utils import save_historical, read_historical, clean_symbol
from src.application import conf
from src.infraestructure.crypto.exchange_model import Trading as Trading_Crypto
from src.infraestructure.mt4.mt4_model import Trading as Trading_Darwinex


logger = logging.getLogger(__name__)


def save_test_data():
    """ Save test data for testing purposes """
    path = os.path.join(conf.path_modulo, 'crypto', '../data/data_crypto')
    # check files in folder if pkl
    files = [f for f in os.listdir(path) if f.endswith('.pkl')]
    for file in files:
        df = pd.read_pickle(os.path.join(path, file), compression='gzip')
        save_historical(file.split('.')[0], df, name_library='test_historical_1min')


@log_start_end(log=logger)
def historical_downloader(symbols: List[str] = ["EURUSD"], start_date: dt.datetime = dt.datetime(2022, 7, 1),
                          end_date: dt.datetime = dt.datetime.utcnow(),
                          interval: str = '1m', provider: str = 'darwinex', clean_symbols_database: list = []):
    """ Main function """
    name_library = f'{provider}_historical_{interval}'
    # Connect to the exchange or broker
    if provider == 'darwinex':
        config_broker = {'DWT_FTP_USER': conf.DWT_FTP_USER, 'DWT_FTP_PASS': conf.DWT_FTP_PASS,
                         'DWT_FTP_HOSTNAME': conf.DWT_FTP_HOSTNAME, 'DWT_FTP_PORT': conf.DWT_FTP_PORT}
        trading = Trading_Darwinex(config_broker=config_broker)
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
    provider = 'darwinex'
    interval = '1m'
    symbols = ['AUDNZD', 'GBPUSD']  # List of symbols to download from provider
    start_date = dt.datetime(2022, 9, 1)  # Start date of data to download
    end_date = dt.datetime.utcnow()  # End date of data to download
    # Interval of data to download,
    historical_downloader(symbols=symbols, start_date=start_date, end_date=dt.datetime.utcnow(),
                          provider=provider, clean_symbols_database=symbols, interval=interval)


