from smartbots.database_handler import Universe
import pandas as pd
import datetime as dt
from datetime import timedelta
import warnings
import numpy as np
import schedule
import time
warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)

"""Script to update historical betfair"""


def read_data(lib, symbol):
    """Read data from MongoDB"""
    data = lib.read(symbol).data
    if data.event_type == 'odds':
        try:
            dict_per_event[data.unique_name].append(data.__dict__)
        except:
            dict_per_event[data.unique_name] = []
            dict_per_event[data.unique_name].append(data.__dict__)
        if data.last_row == 1:
            save_historical_data()


def save_historical_data():
    global dict_per_event
    #  Save data in new library
    for k in list(dict_per_event):
        df = pd.DataFrame(dict_per_event[k])
        datetime_df = pd.to_datetime(df['datetime'].values[0])
        search_last_row = df[df['last_row'] == 1]
        if len(search_last_row) > 0:
            # sort df by datetime
            del dict_per_event[k]
            df = df.sort_values(by=['datetime'])
            df.index = df['datetime']
            df.index.name = 'date'
            lib_historical_betfair.write(df['unique_name'].values[0], df, metadata={'datetime': datetime_df,
                                                                                    'ticker': df['ticker'].values[0],
                                                                                    'selection': df['selection'].values[
                                                                                        0],
                                                                                    'competition':
                                                                                        df['competition'].values[0],
                                                                                    'match_name':
                                                                                        df['match_name'].values[0],
                                                                                    'sport_id': int(
                                                                                        df['sports_id'].values[0])})

def update_mongodb():
    global dict_per_event, lib_historical_betfair

    dict_per_event = {}
    control_yesterday = set()
    control_betfair_historical = set()
    control_has_symbol = set()
    today = dt.datetime.utcnow()
    name = f'{name_library}_{today.strftime("%Y%m%d")}'
    yesterday = today - timedelta(days=1)
    name_yesterday = f'{name_library}_{yesterday.strftime("%Y%m%d")}'
    store = Universe()
    # libraries
    lib_keeper = store.get_library(name)
    lib_keeper_yesterday = store.get_library(name_yesterday)
    lib_historical_betfair = store.get_library('betfair_files_historical')
    list_symbols = lib_keeper.list_symbols(regex="over")
    list_symbols_yesterday = lib_keeper_yesterday.list_symbols(regex="over")
    for sim in list_symbols:
        if 'None' in sim:
            last_part = len(sim.split('_')[-1]) + 1
        else:
            last_part = len(sim.split('_')[-1] + sim.split('_')[-2]) + 2
        # check if this symbol is in lib_historical_betfair
        if sim[:-last_part] not in control_betfair_historical and sim[:-last_part] not in control_has_symbol:
            if lib_historical_betfair.has_symbol(sim[:-last_part]) is False:
                control_betfair_historical.add(sim[:-last_part])
            else:
                control_has_symbol.add(sim[:-last_part])
        # this symbol is not in historical
        if sim[:-last_part] in control_betfair_historical:
            if sim[:-last_part] not in control_yesterday:
                control_yesterday.add(sim[:-last_part])
                list_filter_yesterday = [l for l in list_symbols_yesterday if sim[:-last_part] in l]
                if len(list_filter_yesterday) > 0:
                    # this event has data from yesterday
                    for sim_yes in list_filter_yesterday:
                        read_data(lib_keeper_yesterday, sim_yes)

            read_data(lib_keeper, sim)

    #  Remove library from two days ago
    date = yesterday - timedelta(days=1)
    name_delete = f'{name_library}_{date.strftime("%Y%m%d")}'
    store.client.delete_library(name_delete)


def main():
    """ Main function """
    # create scheduler for update db
    schedule.every().hour.at(":58").do(update_mongodb)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    """ Update mongo db"""
    name_library = 'events_keeper'

    main()