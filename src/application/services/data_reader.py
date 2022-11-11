""" Load data from DB and create Events for consumption by portfolio engine
  Doc: https://github.com/man-group/arctic/wiki/Chunkstore
 """
import pandas as pd
import datetime as dt
from src.domain.events import Bar, Tick, Timer
from src.infraestructure.database_handler import Universe


def read_data_to_dataframe(symbol:str, provider:str, interval:str = '1m',
                           start_date: dt.datetime = dt.datetime(2022, 1, 1),
                           end_date: dt.datetime = dt.datetime.utcnow()):

    """ Read data from DB and create DataFrame"""
    store = Universe()  # database handler
    name_library = f'{provider}_historical_{interval}'
    lib = store.get_library(name_library)
    end_date = end_date + dt.timedelta(days=1)
    df = lib.read(symbol, chunk_range=pd.date_range(start_date, end_date))

    return df


def load_tickers_and_create_events(symbols_lib_name: list, start_date: dt.datetime = dt.datetime(2022, 1, 1),
                                   end_date: dt.datetime = dt.datetime.utcnow()):
    """ Load data from DB and create Events for consumption by portfolio engine
        symbols_lib_name: list of symbols to load with info about the source of the data
        start_date: start date of the query period
        end_date: end date of the query period """

    # Create list of ticker and library name
    symbols_to_read = []
    for info in symbols_lib_name:
        if 'tickers' in info:
            for t in info['tickers']:
                symbols_to_read.append({'ticker': t, 'historical_library': info['historical_library']})
        elif 'ticker' in info:
            symbols_to_read.append(info)
        else:
            raise ValueError('No tickers or ticker in info')

    store = Universe() # database handler
    # get_chunk_ranges save
    _ranges_save = []
    for info in symbols_to_read:
        ticker_name =info['ticker']
        name_library = info['historical_library']
        lib = store.get_library(name_library)
        if lib.has_symbol(ticker_name):
            list_symbol = [[pd.to_datetime(d[0].decode("utf-8")),pd.to_datetime(d[1].decode("utf-8"))]
                           for d in list(lib.get_chunk_ranges(ticker_name))]

            frame = pd.DataFrame(list_symbol, columns=['start_date', 'end_date'])
            frame['ticker'] = ticker_name
            _ranges_save.append(frame)

    ranges_save = pd.concat(_ranges_save)
    ranges_save = ranges_save.drop_duplicates(subset=['start_date'])
    ranges_save = ranges_save.sort_values(by=['start_date'])
    # filter
    ranges_save = ranges_save[ranges_save['start_date'] >= start_date]
    ranges_save = ranges_save[ranges_save['start_date'] <= end_date]
    day = {}
    ant_close = {}

    for month in ranges_save.itertuples():
        datas = []
        for info in symbols_to_read:
            ticker_name = info['ticker']
            name_library = info['historical_library']
            lib = store.get_library(name_library)
            if lib.has_symbol(ticker_name):
                print(f'Loading {ticker_name} from {month.start_date}')
                month_end = month.end_date + dt.timedelta(days=1)
                data = lib.read(ticker_name, chunk_range=pd.date_range(month.start_date, month_end))
                if len(data):
                    data['event_type'] = 'bar'
                    if 'multiplier' not in data.columns:
                        data['multiplier'] = 1 # default value
                    if 'ask' not in data.columns:
                        data['ask'] = data['close']
                    if 'bid' not in data.columns:
                        data['bid'] = data['close']
                    if len(data) > 0:
                        datas.append(data)
                        if ticker_name not in day:  # fill day with the first day of the month
                            day[ticker_name] = data.index.min().day - 1
                            ant_close[ticker_name] = {'close':data.iloc[0].close,'datetime':data.index.min()}

        today = dt.datetime.utcnow()
        month_end_date = month.end_date
        if month_end_date > today:
            month_end_date = today
        # create timer
        timer_index = pd.date_range(month.start_date, month_end_date, freq='2min')
        df_timer = pd.DataFrame(index=timer_index)
        df_timer['event_type'] = 'timer'
        datas.append(df_timer)

        ### Sort and Send events to portfolio engine
        if len(datas) > 0:
            df = pd.concat(datas)
            df.sort_index(inplace=True)
            for tuple in df.itertuples():
                # create bar event  for the frecuency of the data
                event_type = tuple.event_type
                if event_type == 'bar':
                    bar = Bar(ticker=tuple.symbol, datetime=tuple[0], open=tuple.open, high=tuple.close, low=tuple.low,
                              close=tuple.close, volume=tuple.volume, exchange=tuple.exchange_or_broker, multiplier=tuple.multiplier,
                              ask=tuple.ask, bid=tuple.bid)


                    if day[bar.ticker] != bar.datetime.day: # change of day
                        day[bar.ticker] = bar.datetime.day
                        tick = Tick(event_type='tick', tick_type='close_day', price=ant_close[bar.ticker]['close'],
                                    ticker=bar.ticker, datetime=ant_close[bar.ticker]['datetime'])
                        yield tick # send close_day event
                    yield bar # send bar event
                    ant_close[bar.ticker] = {'close':bar.close,'datetime': bar.datetime}

                    
                elif event_type == 'timer':
                    timer = Timer(datetime=tuple[0])
                    yield timer  # send timer event

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
