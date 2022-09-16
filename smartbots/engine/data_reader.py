""" Load data from DB and create Events for consumption by portfolio engine """
import pandas as pd
import datetime as dt
from smartbots.events import Bar, Odds, Tick
from smartbots.database_handler import Universe
import calendar
from dateutil import relativedelta

def read_data_to_dataframe(symbol:str, provider:str, interval:str = '1min',
                           start_date: dt.datetime = dt.datetime(2022, 1, 1),
                           end_date: dt.datetime = dt.datetime.utcnow()):

    """ Read data from DB and create DataFrame"""
    store = Universe()  # database handler
    name_library = f'{provider}_historical_{interval}'
    lib = store.get_library(name_library)

    from_month = start_date
    end_month = calendar.monthrange(from_month.year, from_month.month)
    to_month = dt.datetime(from_month.year, from_month.month, end_month[1], 23, 59)
    yyyymm = from_month.strftime('%Y%m')

    datas = []
    while True:
        ticker = symbol + '_' + yyyymm
        if lib.has_symbol(ticker):
            data = lib.read(ticker).data
            data = data[data.index <= to_month]
            datas.append(data)

        # update month
        from_month = from_month + relativedelta.relativedelta(months=1)
        from_month = dt.datetime(from_month.year, from_month.month, 1)  # first day of the month
        end_month = calendar.monthrange(from_month.year, from_month.month)
        to_month = dt.datetime(from_month.year, from_month.month, end_month[1], 23, 59)
        yyyymm = from_month.strftime('%Y%m')

        if to_month >= end_date + relativedelta.relativedelta(months=1):  # break if we reach the end of the period
            break


    ### Join all dataframes
    if len(datas) > 0:
        df = pd.concat(datas)
        df.sort_index(inplace=True)
        df['close'] = [c.close for c in df['bar'].values ]

    return df


def load_tickers_and_create_events(symbols_lib_name: list, start_date: dt.datetime = dt.datetime(2022, 1, 1),
                                   end_date: dt.datetime = dt.datetime.utcnow()):
    """ Load data from DB and create Events for consumption by portfolio engine
        symbols_lib_name: list of symbols to load with info about the source of the data
        start_date: start date of the query period
        end_date: end date of the query period """

    store = Universe() # database handler

    from_month = start_date
    end_month = calendar.monthrange(from_month.year, from_month.month)
    to_month = dt.datetime(from_month.year, from_month.month, end_month[1], 23, 59)
    yyyymm = from_month.strftime('%Y%m')
    day = {}
    ant_bar = {}
    while True:
        datas = []
        for info in symbols_lib_name:
            symbols_to_read = []
            if 'tickers' in info:
                for t in info['tickers']:
                    symbols_to_read.append(t +'_'+ yyyymm)
                    day.setdefault(t, None)
                    ant_bar.setdefault(t, None)
            elif 'ticker' in info:
                symbols_to_read.append(info['ticker'] + '_' + yyyymm)
            else:
                raise ValueError('No tickers or ticker in info')
            for symbol in symbols_to_read:
                ticker_name = symbol.split('_')[0]
                name_library = info['historical_library']
                print(f'{symbol}')
                lib = store.get_library(name_library)
                if lib.has_symbol(symbol):
                    data = lib.read(symbol).data
                    data = data[data.index <= to_month]
                    datas.append(data)
                    if ticker_name not in day: # fill day with the first day of the month
                        day[ticker_name] = data.index.min().day - 1
                        ant_bar[ticker_name] = data.iloc[0].bar

        ### Sort and Send events to portfolio engine
        if len(datas) > 0:
            df = pd.concat(datas)
            df.sort_index(inplace=True)
            col_name = df.columns[0]
            for tuple in df.itertuples():
                t = tuple.bar
                if day[t.ticker] != t.datetime.day and ant_bar[t.ticker] is not None: # change of day
                    day[t.ticker] = t.datetime.day
                    tick = Tick(event_type='tick', tick_type='close_day', price=ant_bar[t.ticker].close,
                                      ticker=t.ticker, datetime=ant_bar[t.ticker].datetime)
                    yield tick # send close_day event
                yield t # send bar event
                ant_bar[t.ticker] = t

        # update month
        from_month = from_month + relativedelta.relativedelta(months=1)
        from_month = dt.datetime(from_month.year, from_month.month, 1)  # first day of the month
        end_month = calendar.monthrange(from_month.year, from_month.month)
        to_month = dt.datetime(from_month.year, from_month.month, end_month[1], 23, 59)
        yyyymm = from_month.strftime('%Y%m')

        if to_month >= end_date + relativedelta.relativedelta(months=1):  # break if we reach the end of the period
            break

def load_tickers_and_create_events_betting(tickers_lib_name: list, start_date: dt.datetime = dt.datetime(2022, 1, 1),
                                           end_date: dt.datetime = dt.datetime.utcnow()):
    """ Load data from DB and create Events for consumption by portfolio engine for betting markets
        tickers_lib_name: list of tickers to load with info about the source of the data
         """
    store = Universe()
    yyyymmdd_start = start_date.year * 10000 + start_date.month * 100 + start_date.day
    yyyymmdd_end = end_date.year * 10000 + end_date.month * 100 + end_date.day
    for info in tickers_lib_name:
        ticker = info['ticker']
        name_library = info['historical_library']
        lib = store.get_library(name_library)
        list_symbols = [l for l in lib.list_symbols() if
                        ticker in l and yyyymmdd_start <= int(l.split('_')[-1]) <= yyyymmdd_end]

        for symbol in list_symbols:
            data = lib.read(symbol).data
            data.sort_index(inplace=True)
            for tuple in data.itertuples():
                yield tuple
