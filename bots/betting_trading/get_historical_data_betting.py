""" Historical data from Kucoin"""
import logging
import os
import datetime as dt
from smartbots import conf
from typing import List,Dict
import pandas as pd
from arctic import Arctic
from smartbots.decorators import log_start_end

logger = logging.getLogger(__name__)

def _get_historical_data_test_files_betfair():
    """ Read historical data save in file, normalice it and return it as events"""
    from smartbots.events import Odds
    location = os.path.join(conf.path_modulo, 'betting', 'data', 'test_data')
    files = os.listdir(location)
    datas = {}

    normalize_columns = {'dt_actual_off': 'datetime_real_off',
                         'scheduled_off': 'datetime_scheduled_off',
                         'encuentro': 'match_name',
                         'equipo_local': 'local_team',
                         'equipo_visitante': 'away_team',
                         'id_local': 'local_team_id',
                         'id_visitante': 'away_team_id',
                         'id_partido': 'match_id',
                         'lastpricetraded':'odds_last_traded',
                          'unico':'unique_id_match',
                          'unico_evento':'unique_id_ticker',
                          'id_competition':'competition_id',
                          'sortPriority':'sort_priority',
                          'event':'ticker',
                           'event_id':'ticker_id',
                         }

    for file in files:
        events = []
        df = pd.read_csv(os.path.join(location, file), sep=';')
        df.columns = [str(c) for c in df.columns]
        # rename columns dataframe
        df.rename(columns=normalize_columns, inplace=True)
        df.index = pd.to_datetime(df['datetime'], unit='s')
        df['datetime_real_off'] = pd.to_datetime(df['datetime_real_off'], unit='s')
        df['datetime_scheduled_off'] = pd.to_datetime(df['datetime_scheduled_off'], unit='s')
        df.drop(['datetime'], axis=1, inplace=True)
        unique_name =df['match_name'].values[0] +'_' +df.unique_id_ticker.values[0]
        df['unique_name'] = unique_name
        # Creamos eventos Odds
        for tuple in df.itertuples():
            events.append(Odds(datetime=tuple.Index, ticker=tuple.ticker,
                               unique_name=tuple.unique_name, unique_id_match=tuple.unique_id_match,
                               unique_id_ticker=tuple.unique_id_ticker,
                               selection=tuple.selection, selection_id=tuple.selection_id,
                               ticker_id=tuple.ticker_id, competition=tuple.competition,
                               days_since_last_run=tuple.days_since_last_run,
                               match_name=tuple.match_name, local_team=tuple.local_team, away_team=tuple.away_team,
                               full_description=tuple.full_description, competition_id=tuple.competition_id,
                               local_team_id=tuple.local_team_id, away_team_id=tuple.away_team_id,
                               match_id=tuple.match_id, in_play=tuple.in_play,
                               jockey_name=tuple.jockey_name, odds_last_traded=tuple.odds_last_traded,
                               number_of_active_runners=tuple.number_of_active_runners,
                               number_of_winners=tuple.number_of_winners,
                               odds_back=[tuple.odds_back, tuple.odds_back_1, tuple.odds_back_2, tuple.odds_back_3],
                               odds_lay=[tuple.odds_lay, tuple.odds_lay_1, tuple.odds_lay_2, tuple.odds_lay_3],
                               size_back=[tuple.size_back_1, tuple.size_back_2, tuple.size_back_3],
                               size_lay=[tuple.size_lay_1, tuple.size_lay_2, tuple.size_lay_3],
                               official_rating=tuple.official_rating, player_name=tuple.player,
                               trainer_name=tuple.trainer_name, sex_type=tuple.sex_type,
                               sort_priority=tuple.sort_priority, sports_id=tuple.sports_id,
                               status=tuple.status, status_selection=tuple.status_selection,
                               volume_matched=tuple.volume_matched, win_flag=tuple.win_flag))

        df_save = pd.DataFrame({'odds':events},index = df.index)
        df_save.index.name = 'date'
        datas[unique_name] = df_save
    return datas



def save_historical(symbol_data :Dict = {},name_library: str= 'provider_historical') -> None:
    """ Save historical data in Data Base as VersionStore.
        Here the docs: https://github.com/man-group/arctic"""
    store = Arctic(f'{conf.MONGO_HOST}:{conf.MONGO_PORT}',username=conf.MONGO_INITDB_ROOT_USERNAME,
                   password=conf.MONGO_INITDB_ROOT_PASSWORD)
    store.initialize_library(name_library)
    lib = store[name_library]

    for symbol, data in symbol_data.items():
        data.index.name = 'date'
        ticker = str(data['odds'].iloc[0].ticker)
        dtime = data['odds'].iloc[0].datetime_scheduled_off #.to_pydatetime()
        selection = str(data['odds'].iloc[0].selection)
        sports_id = int(data['odds'].iloc[0].sports_id)
        lib.write(symbol, data, metadata={'ticker': ticker,
                                          'datetime': dtime,
                                          'selection':selection, 'sport_id': sports_id})


@log_start_end(log=logger)
def main(provider='betfair_files'):
    """ Main function """
    if provider == 'betfair_files':
         get_historical_data = _get_historical_data_test_files_betfair
    else:
        raise ValueError(f'Provider {provider} not implemented')

    data = get_historical_data()
    save_historical(data, name_library=f'{provider}_historical')
    print(f'* Historical data for {provider} saved')

if __name__ == '__main__':
    """ A temp file it is save until completed, you can re-run this script if something goes wrong """
    main(provider='betfair_files')
