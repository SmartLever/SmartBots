from smartbots.database_handler import Universe
import pandas as pd
import datetime as dt

"""Database related methods"""

def read_historical(symbol: str, name_libray_historical: str = 'darwinex_historical_1min',
                    start_date: dt.datetime = dt.datetime(2022, 7, 1),
                    end_date: dt.datetime = dt.datetime.utcnow(),last_month: bool=False) -> pd.DataFrame:
    """ Read historical data from initial month and end month.
        Symbols as save as :symbol_monthYear as a way to identify the data.
        """
    store = Universe()
    lib = store.get_library(name_libray_historical)
    if lib.has_symbol(symbol) is False:
        return pd.DataFrame()
    try:
        if last_month: # read last month of data
            last_month_range = list(lib.get_chunk_ranges(symbol))[-1]
            end_date = pd.to_datetime(last_month_range[1].decode("utf-8") ) + dt.timedelta(days=1)
            start_date = pd.to_datetime(last_month_range[0].decode("utf-8") )
        else:
            end_date = end_date + dt.timedelta(days=1)
    except:
        return pd.DataFrame()
    return lib.read(symbol, chunk_range=pd.date_range(start_date, end_date))


def save_historical(symbol: str, data: pd.DataFrame, name_library: str = 'darwinex_historical_1min') -> None:
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