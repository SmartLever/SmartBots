""" Historical data from Kucoin"""
import os
from smartbots import conf
from typing import Dict
import pandas as pd
from smartbots.database_handler import Universe

def _get_historical_data_test_files_betfair():
    """ Read historical data save in file, normalise it and return it as events"""
    from smartbots.events import Odds
    location = os.path.join(conf.path_modulo, 'betting', 'data', 'test_data')
    files = os.listdir(location)
    data = {}

    normalize_columns = {'dt_actual_off': 'datetime_real_off',
                         'scheduled_off': 'datetime_scheduled_off',
                         'encuentro': 'match_name',
                         'equipo_local': 'local_team',
                         'equipo_visitante': 'away_team',
                         'id_local': 'local_team_id',
                         'id_visitante': 'away_team_id',
                         'id_partido': 'match_id',
                         'lastpricetraded': 'odds_last_traded',
                         'unico': 'unique_id_match',
                         'unico_evento': 'unique_id_ticker',
                         'id_competition': 'competition_id',
                         'sortPriority': 'sort_priority',
                         'event': 'ticker',
                         'event_id': 'ticker_id',
                         'ultima': 'last_row'
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
        unique_name = df['match_name'].values[0] + '_' + df.unique_id_ticker.values[0] + '_' + str(
            df.selection_id.values[0])
        df['unique_name'] = unique_name
        # Create events Odds
        for tp in df.itertuples():
            events.append(Odds(datetime=tp.Index, ticker=tp.ticker,
                               unique_name=tp.unique_name, unique_id_match=tp.unique_id_match,
                               unique_id_ticker=tp.unique_id_ticker,
                               selection=tp.selection, selection_id=tp.selection_id,
                               ticker_id=tp.ticker_id, competition=tp.competition,
                               days_since_last_run=tp.days_since_last_run,
                               match_name=tp.match_name, local_team=tp.local_team, away_team=tp.away_team,
                               full_description=tp.full_description, competition_id=tp.competition_id,
                               last_row=tp.last_row, local_team_id=tp.local_team_id,
                               away_team_id=tp.away_team_id, match_id=tp.match_id, in_play=tp.in_play,
                               jockey_name=tp.jockey_name, odds_last_traded=tp.odds_last_traded,
                               number_of_active_runners=tp.number_of_active_runners,
                               number_of_winners=tp.number_of_winners,
                               odds_back=[tp.odds_back, tp.odds_back_1, tp.odds_back_2, tp.odds_back_3],
                               odds_lay=[tp.odds_lay, tp.odds_lay_1, tp.odds_lay_2, tp.odds_lay_3],
                               size_back=[tp.size_back_1, tp.size_back_2, tp.size_back_3],
                               size_lay=[tp.size_lay_1, tp.size_lay_2, tp.size_lay_3],
                               official_rating=tp.official_rating, player_name=tp.player,
                               trainer_name=tp.trainer_name, sex_type=tp.sex_type,
                               sort_priority=tp.sort_priority, sports_id=tp.sports_id,
                               status=tp.status, status_selection=tp.status_selection,
                               volume_matched=tp.volume_matched, win_flag=tp.win_flag))

        df_save = pd.DataFrame({'odds': events}, index=df.index)
        df_save.index.name = 'date'
        data[unique_name] = df_save
    return data


def save_historical(symbol_data: Dict = {}, name_library: str = 'provider_historical') -> None:
    """ Save historical data in Data Base as VersionStore.
        Here the docs: https://github.com/man-group/arctic"""

    store = Universe()
    lib = store.get_library(name_library, library_chunk_store=False)

    for symbol, data in symbol_data.items():
        data.index.exchange_or_broker = 'date'
        ticker = str(data['odds'].iloc[0].ticker)
        dtime = data['odds'].iloc[0].datetime_scheduled_off  # to_pydatetime()
        selection = str(data['odds'].iloc[0].selection)
        sports_id = int(data['odds'].iloc[0].sports_id)
        lib.write(symbol, data, metadata={'ticker': ticker,
                                          'datetime': dtime,
                                          'selection':selection, 'sport_id': sports_id})


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