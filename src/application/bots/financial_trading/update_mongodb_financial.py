from src.infraestructure.database_handler import Universe
import pandas as pd
import datetime as dt
from datetime import timedelta
import schedule
import time
from src.application.services.historical_utils import read_historical, save_historical
from src.application import conf

"""Script to update historical with mongodb data"""


def main():
    """ Main function """

    def read_data(lib, symbol):
        """Read data from MongoDB"""
        try:
            data = lib.read(symbol).data
            if data.event_type == 'bar':
                try:
                    dict_per_ticker[data.ticker].append(data.__dict__)
                except:
                    dict_per_ticker[data.ticker] = []
                    dict_per_ticker[data.ticker].append(data.__dict__)
        except:
            pass

    def update_mongodb():

        global dict_per_ticker
        dict_per_ticker = {}
        today = dt.datetime.utcnow()
        name = f'{name_library}_{today.strftime("%Y%m%d")}'
        yesterday = today - timedelta(days=1)
        name_yesterday = f'{name_library}_{yesterday.strftime("%Y%m%d")}'
        store = Universe()
        # libraries
        lib_keeper = store.get_library(name, library_chunk_store=False)
        lib_keeper_yesterday = store.get_library(name_yesterday, library_chunk_store=False)
        print(dt.datetime.utcnow())
        for ticker in tickers:
            # Read historical data
            data_last = read_historical(ticker, name_libray_historical, last_month=True)
            # Pass to datetime
            data_last['datetime'] = pd.to_datetime(data_last['datetime'], format='%Y-%m-%d %H:%M:%S')
            data_last.index = data_last['datetime']
            max_index_historical = data_last.index.max()
            # same day, don't read symbols from yesterday
            if max_index_historical.day == today.day:
                # range of dates from last data
                list_dates = pd.date_range(max_index_historical, today, freq='1min')
                list_symbols_yesterday = []
                list_symbols_today = [f'{ticker}_{x.strftime("%Y-%m-%d %H:%M:00")}_bar' for x in list_dates]
            # different day, read symbols from yesterday
            else:
                # calculate end of the day from the last data
                end_day = dt.datetime(max_index_historical.year, max_index_historical.month,
                                      max_index_historical.day, 23, 59, 0)
                # range of dates from last data
                list_dates = pd.date_range(max_index_historical, end_day, freq='1min')
                list_symbols_yesterday = [f'{ticker}_{x.strftime("%Y-%m-%d %H:%M:00")}_bar' for x in list_dates]
                list_symbols_today = lib_keeper.list_symbols(regex=ticker)

            for sim in list_symbols_today:
                read_data(lib_keeper, sim)
            for sim in list_symbols_yesterday:
                read_data(lib_keeper_yesterday, sim)

            data = pd.DataFrame(dict_per_ticker[ticker])
            # Sort data
            data = data.sort_values(by=['datetime'])
            data.index = data['datetime']
            data['symbol'] = data['ticker']
            if len(data) > 0 and len(data_last) > 0:  #
                # update data
                data = data[data.index > data_last.index.max() - timedelta(days=1)]
                data = pd.concat([data_last, data])

            if len(data) > 0:  # save data
                save_historical(ticker, data, name_libray_historical)
            # clean dict_per_ticker
            dict_per_ticker = {}

        #  Remove library from two days ago
        date = yesterday - timedelta(days=1)
        name_delete = f'{name_library}_{date.strftime("%Y%m%d")}'
        store.client.delete_library(name_delete)

    name_library = 'events_keeper'
    name_libray_historical = 'darwinex_historical_1min'
    tickers = conf.FINANCIAL_SYMBOLS

    # create scheduler for update db
    schedule.every().hour.at(":41").do(update_mongodb)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    """ Update mongo db"""
    main()