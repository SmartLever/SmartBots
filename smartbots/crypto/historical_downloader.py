""" Download historical data frrom Data Exchage and save it for use in the bot.  """
import logging
import os
import datetime as dt
from typing import List
import pandas as pd
from smartbots.database_handler import Universe
from smartbots.decorators import log_start_end
from smartbots.events import Bar
from smartbots import conf
from smartbots.crypto.exchange_model import Trading

logger = logging.getLogger(__name__)


def dataframe_to_bars(symbol: str, frame: pd.DataFrame):
    events = []
    for tuple in frame.itertuples():
        events.append(Bar(datetime=tuple.Index, ticker=symbol, open=tuple.open, high=tuple.high,
                          low=tuple.low, close=tuple.close, volume=tuple.volume))
    df = pd.DataFrame({'bar': events}, index=frame.index)
    df.index.exchange = 'date'
    return df


def save_test_data():
    """ Save test data for testing purposes """
    path = os.path.join(conf.path_modulo, 'crypto', 'data')
    # check files in folder if pkl
    files = [f for f in os.listdir(path) if f.endswith('.pkl')]
    for file in files:
        df = pd.read_pickle(os.path.join(path, file), compression='gzip')
        save_historical(file.split('.')[0], df, name_library='test_historical_1min')


def save_historical(symbol: str, data: pd.DataFrame, name_library: str = 'provider_historical_1min') -> None:
    """ Save historical in database in the library."""
    store = Universe()
    lib = store.get_library(name_library)
    # save in chunks of 1 month of data, index have to be a datetime object with name date
    data.index.name = 'date'
    lib.write(symbol, data, chunk_size='M', metadata={'symbol': symbol, 'end_date': data.index[-1]})
    print(f'Symbol {symbol} saved.')


def read_historical(symbol: str, name_library: str = 'provider_historical_1min',
                    start_date: dt.datetime = dt.datetime(2022, 7, 1),
                    end_date: dt.datetime = dt.datetime.utcnow(),last_month: bool=False) -> pd.DataFrame:
    """ Read historical data from initial month and end month.
        Symbols as save as :symbol_monthYear as a way to identify the data.
        """
    store = Universe()
    lib = store.get_library(name_library)
    if lib.has_symbol(symbol) is False:
        return pd.DataFrame()
    if last_month: # just read last month of data
        last_month_range = list(lib.get_chunk_ranges(symbol))[-1]
        end_date = pd.to_datetime(last_month_range[1].decode("utf-8") )
        start_date = pd.to_datetime(last_month_range[0].decode("utf-8") )
    else:
        end_date = end_date + dt.timedelta(days=1)
    return lib.read(symbol, chunk_range=pd.date_range(start_date, end_date))


def clean_symbol(symbols, name_library):
    store = Universe()
    lib = store.get_library(name_library)
    for symbol in symbols:
        for _s in lib.list_symbols():
            if symbol in _s:
                lib.delete(_s)
                print(f'Symbol {_s} deleted.')


@log_start_end(log=logger)
def historical_downloader(symbols: List[str] = ["BTC-USDT"], start_date: dt.datetime = dt.datetime(2022, 7, 1),
                          end_date: dt.datetime = dt.datetime.utcnow(),
                          interval: str = '1m', provider: str = 'kucoin', clean_symbols_database: list = []):
    """ Main function """
    name_library = f'{provider}_historical_{interval}'

    # Connect to the exchange
    trading = Trading(exchange=provider)
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
            if c not in ['symbol', 'datetime', 'exchange']:
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
    historical_downloader(symbols=["ETH-USDT"],
                          start_date=dt.datetime(2022, 9, 28))
