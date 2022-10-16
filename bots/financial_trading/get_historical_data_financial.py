""" Historical data from Financial"""
import os
from smartbots import conf
from typing import Dict
import pandas as pd
from smartbots.database_handler import Universe

def _get_historical_data(name_library):
    """ Read historical data save in file, return it as events"""
    from smartbots.events import Bar
    location = os.path.join(conf.path_modulo, 'financial', 'data', 'test_data')
    files = os.listdir(location)
    data = {}
    for file in files:
        df = pd.read_csv(os.path.join(location, file), sep=',')
        df.columns = [str(c) for c in df.columns]
        df['ticker'] = df['contract']
        df['symbol'] = df['contract']
        df['exchange'] = 'mt4_darwinex'
        df['provider'] = 'mt4_darwinex'
        df['freq'] = '1min'
        df['datetime'] = df['date_time']
        df['dtime_zone'] = 'UTC'
        # rename columns dataframe
        df.rename(columns={"multiplicador": "multiplier"},inplace=True)
        df.index = pd.to_datetime(df['datetime'])
        df.drop(['date_time'], axis=1, inplace=True)
        unique_name = df['contract'].values[0]
        df.index.name = 'date'
        save_historical(unique_name, df, name_library)

    return data


def save_historical(symbol: str, data: pd.DataFrame, name_library: str = 'provider_historical_1min') -> None:
    """ Save historical in database in the library."""
    store = Universe()
    lib = store.get_library(name_library)
    # save in chunks of 1 month of data, index have to be a datetime object with name date
    data.index.name = 'date'
    if lib.has_symbol(symbol):
        lib.update(symbol, data, chunk_size='M')
    else:
        lib.write(symbol, data, chunk_size='M')
    print(f'Symbol {symbol} saved.')


def main():
    """ Main function """
    provider = 'darwinex'
    name_library = f'{provider}_historical_1min'
    _get_historical_data(name_library)


if __name__ == '__main__':
    """ A temp file it is save until completed, you can re-run this script if something goes wrong """
    main()