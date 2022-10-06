""" Historical data from Financial"""
import logging
import os
from smartbots import conf
from typing import Dict
import pandas as pd
from smartbots.decorators import log_start_end
from smartbots.database_handler import Universe
logger = logging.getLogger(__name__)

def _get_historical_data():
    """ Read historical data save in file, return it as events"""
    from smartbots.events import Bar
    location = os.path.join(conf.path_modulo, 'financial', 'data', 'test_data')
    files = os.listdir(location)
    data = {}
    for file in files:
        events = []
        df = pd.read_csv(os.path.join(location, file), sep=',')
        df.columns = [str(c) for c in df.columns]
        # rename columns dataframe
        df.index = pd.to_datetime(df['date'])
        df.drop(['date'], axis=1, inplace=True)
        unique_name = df['contract'].values[0]
        # Create events Bar
        for tp in df.itertuples():
            events.append(Bar(ticker=tp.contract, datetime=tp.Index, dtime_zone='UTC',
                          open=tp.open,
                          high=tp.high, low=tp.low, close=tp.close,
                          volume=tp.volume, exchange='mt4_darwinex', provider='mt4_darwinex', freq='1min'))

        df_save = pd.DataFrame({'bar': events}, index=df.index)
        df_save.index.exchange = 'date'
        data[unique_name] = df_save
    return data


def save_historical(symbol_data: Dict = {}, name_library: str = 'provider_historical') -> None:
    """ Save historical data in Data Base as VersionStore.
        Here the docs: https://github.com/man-group/arctic"""

    store = Universe()
    lib = store.get_library(name_library)

    for symbol, data in symbol_data.items():
        data['yyyymm'] = data.index.strftime('%Y%m')
        for yyyymm in data['yyyymm'].unique():
            df = data[data['yyyymm'] == yyyymm]
            symbol_save = f'{symbol}_{yyyymm}'
            lib.write(symbol_save, df)
        print(f'Symbol {symbol} saved.')


@log_start_end(log=logger)
def main():
    """ Main function """

    provider = 'darwinex'
    data = _get_historical_data()
    save_historical(data, name_library=f'{provider}_historical_1min')
    print(f'* Historical data for {provider} saved')


if __name__ == '__main__':
    """ A temp file it is save until completed, you can re-run this script if something goes wrong """
    main()