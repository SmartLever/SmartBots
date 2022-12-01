from src.infrastructure.database_handler import Universe
import pandas as pd
import datetime as dt
from src.domain.models.trading.bar import Bar
from src.application import conf

"""Historical related methods

 Doc: https://github.com/man-group/arctic/wiki/Chunkstore

"""


def read_historical(symbol: str, name_library: str = 'provider_historical_1min',
                    start_date: dt.datetime = dt.datetime(2022, 7, 1),
                    end_date: dt.datetime = dt.datetime.utcnow(),last_month: bool=False) -> pd.DataFrame:
    """ Read historical data from initial month and end month.
        Symbols as save as :symbol_monthYear as a way to identify the data.
        """
    store = Universe(host=conf.MONGO_HOST, port=conf.MONGO_PORT)
    lib = store.get_library(name_library)
    if lib.has_symbol(symbol) is False:
        return pd.DataFrame()
    if last_month: # read last month of data
        last_month_range = list(lib.get_chunk_ranges(symbol))[-1]
        end_date = pd.to_datetime(last_month_range[1].decode("utf-8") ) + dt.timedelta(days=1)
        start_date = pd.to_datetime(last_month_range[0].decode("utf-8") )
    else:
        end_date = end_date + dt.timedelta(days=1)
    return lib.read(symbol, chunk_range=pd.date_range(start_date, end_date))


def save_historical(symbol: str, data: pd.DataFrame, name_library: str = 'provider_historical_1min') -> None:
    """ Save historical in database in the library."""
    store = Universe(host=conf.MONGO_HOST, port=conf.MONGO_PORT)
    lib = store.get_library(name_library)
    # save in chunks of 1 month of data, index have to be a datetime object with name date
    data.index.name = 'date'
    if lib.has_symbol(symbol):
        lib.update(symbol, data, chunk_size='M')
    else:
        lib.write(symbol, data, chunk_size='M')
    print(f'Symbol {symbol} saved.')


def get_day_per_month(month, year):
    # Get Max value for a day in given month
    if month in [1, 3, 5, 7, 8, 10, 12]:
        max_day_value = 31
    elif month in [4, 6, 9, 11]:
        max_day_value = 30
    elif year % 4 == 0 and year % 100 != 0 or year % 400 == 0:
        max_day_value = 29
    else:
        max_day_value = 28

    return max_day_value


def clean_symbol(symbols, name_library):
    store = Universe(host=conf.MONGO_HOST, port=conf.MONGO_PORT)
    lib = store.get_library(name_library)
    for symbol in symbols:
        for _s in lib.list_symbols():
            if symbol in _s:
                lib.delete(_s)
                print(f'Symbol {_s} deleted.')


def dataframe_to_bars(symbol: str, frame: pd.DataFrame):
    events = []
    for tuple in frame.itertuples():
        events.append(Bar(datetime=tuple.Index, ticker=symbol, open=tuple.open, high=tuple.high,
                          low=tuple.low, close=tuple.close, volume=tuple.volume))
    df = pd.DataFrame({'bar': events}, index=frame.index)
    df.index.name = 'date'
    return df
