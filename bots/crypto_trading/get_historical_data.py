""" Historical data from Kucoin"""
import logging
import os
import datetime as dt
from smartbots import conf
from typing import List
import pandas as pd
from arctic import Arctic, CHUNK_STORE
from smartbots.decorators import log_start_end

logger = logging.getLogger(__name__)

def save_historical(symbol: str, data: pd.DataFrame,name_library: str= 'provider_historical_1min') -> None:
    """ Save historical data in Data Base using chunk store.
        Here the docs: https://github.com/man-group/arctic/wiki/Chunkstore"""
    store = Arctic(f'{conf.MONGO_HOST}:{conf.MONGO_PORT}',username=conf.MONGO_INITDB_ROOT_USERNAME,
                   password=conf.MONGO_INITDB_ROOT_PASSWORD)
    store.initialize_library(name_library, lib_type=CHUNK_STORE)
    lib = store[name_library]
    # save in chunks of 1 month of data, index have to be a datetime object with name date
    data.index.name = 'date'
    if symbol in lib.list_symbols():
        lib.update(symbol, data, chunk_size='M')
    else:
        lib.write(symbol, data, chunk_size='M')

def read_historical(symbol: str, name_library: str= 'provider_historical_1min') -> pd.DataFrame:
    """ Read historical data from Data Base using chunk store."""
    store = Arctic(f'{conf.MONGO_HOST}:{conf.MONGO_PORT}', username=conf.MONGO_INITDB_ROOT_USERNAME,
                   password=conf.MONGO_INITDB_ROOT_PASSWORD)
    store.initialize_library(name_library, lib_type=CHUNK_STORE)
    lib = store[name_library]
    if symbol in lib.list_symbols():
        return lib.read(symbol)
    return None


@log_start_end(log=logger)
def main(symbols: List[str] =["BTC-USDT"], start_date: dt.datetime=dt.datetime(2022, 7, 1),
         end_date: dt.datetime = dt.datetime.utcnow(),
         interval='1min', provider='kucoin'):
    """ Main function """
    if provider == 'kucoin':
        from smartbots.crypto.kucoin_model import get_historical_data
    else:
        raise ValueError(f'Provider {provider} not implemented')
    # Get historical data
    for symbol in symbols:
        name_library = f'{provider}_historical_{interval}'
        # Check if exist data in DB
        data_last = read_historical(symbol, name_library)
        # if exist data in DB, check if data is complete for the query period
        if data_last is not None: # if exist data in DB, do smart update
            if start_date <= data_last.index.min() + dt.timedelta(days=10):
                # if not, get all data from start_date to end_date
                start_date = data_last.index.max() + dt.timedelta(minutes=1)
                start_date = start_date.to_pydatetime()
        data, temporal_name = get_historical_data(symbol=symbol, interval=interval,
                                                  start_date=start_date, end_date=end_date)

        # change types to float for columns with numeric values (in this case all columns)
        for c in data.columns:
            data[c] = data[c].astype(float)
        if len(data) > 0 and len(data_last) > 0: # update data
            data = pd.concat([data_last, data])
        if len(data) > 0: # save data
            save_historical(symbol, data, name_library=name_library)
        # elimitante temp file
        if os.path.exists(temporal_name):
            os.remove(temporal_name)
        print(f'* Historical data for {symbol} saved')

if __name__ == '__main__':
    """ A temp file it is save until completed, you can re-run this script if something goes wrong """
    main(start_date=dt.datetime(2022, 1, 1), end_date=dt.datetime.utcnow(), provider='kucoin')
