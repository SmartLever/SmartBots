import dataclasses
from typing import Dict
from time import sleep
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from os.path import join
from pathlib import Path
from src.infraestructure.betfair.api import Api
from concurrent.futures import ThreadPoolExecutor, wait
from src.domain.events import Odds
import json
import threading
from src.domain.base_logger import logger
from src.domain.abstractions.abstract_trading_betting import Abstract_Trading

BASE_DIR = Path(__file__).resolve().parent


#######################################################
file_real_actual_off = join(BASE_DIR, 'data_actual_off.json')
# pool for Threads to ask books
pool = ThreadPoolExecutor(10)


def _chunkit(seq: int, num: float):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out


# default Callable
async def _callable(data: dataclasses) -> None:
    """Callback function for realtime data. [Source: Betfair]

    Parameters
    ----------
    data: Dict
        Realtime data.
    """
    print(data)


def _get_parameters(settings: dict, minutes: int, live: bool):
    """Parameters to get events from betfair"""
    start_date = datetime.utcnow() + timedelta(minutes=1)  # 1 minute from now
    end_date = start_date + timedelta(minutes=minutes)  # matches starting in 1-15 mins
    start_date = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    # list of parameters
    parameters = []
    # parameter for live events
    if live:
        for market_types in settings['market_types']:
            params = {'filter': {'eventTypeIds': settings['event_ids'], 'inPlayOnly': True,
                                 'marketTypeCodes': [market_types]},
                      'maxResults': 1000,
                      'marketProjection': ['RUNNER_DESCRIPTION', "COMPETITION", "EVENT",
                                           "EVENT_TYPE", "RUNNER_METADATA",
                                           "MARKET_START_TIME"]
                      }
            parameters.append(params)
    # parameter for next events
    else:
        for market_types in settings['market_types']:
            params = {
                'filter': {
                    'eventTypeIds': settings['event_ids'],
                    'marketStartTime': {
                        'from': start_date,
                        'to': end_date
                    },
                    'marketTypeCodes': [market_types],  # e.g. ['MATCH_ODDS']# e.g. ['ODDS']
                },
                'marketProjection': ['RUNNER_DESCRIPTION', "COMPETITION", "EVENT", "EVENT_TYPE", "RUNNER_METADATA",
                                     "MARKET_START_TIME"],
                'maxResults': 1000,
                'sort': 'FIRST_TO_START'  # sort in start time order
            }
            parameters.append(params)
    return parameters


def _load_actual_off():
    """Load actual off file"""
    # if it not exists we create an empty file
    if not os.path.isfile(file_real_actual_off):
        with open(file_real_actual_off, 'w') as f:
            json.dump({'datetime_real_off': {}, 'start': {}}, f)  # key: match

    try:
        with open(file_real_actual_off, 'r') as json_data:
            data = json.load(json_data)
    except:
        os.remove(file_real_actual_off)
        with open(file_real_actual_off, 'w') as f:
            json.dump({'datetime_real_off': {}, 'start': {}}, f)  # key: match
        with open(file_real_actual_off, 'r') as json_data:
            data = json.load(json_data)
    return data


class Trading(Abstract_Trading):
    """Class for trading Betting on Betfair.

    Attributes
    ----------
    client: Client
        Betfair client.
    """

    def __init__(self, settings_real_time: dict = {}, callback_real_time: callable = _callable,
                 exchange_or_broker: str = 'betfair', config_broker: Dict = {}):
        """Initialize class."""
        super().__init__(settings_real_time=settings_real_time, callback_real_time=callback_real_time,
                         exchange_or_broker=exchange_or_broker, config_broker=config_broker)
        self.client = self.get_client()
        self.data_actual_off = _load_actual_off()

    def get_client(self):
        """Get Betfair client.

        Returns
        -------
        Client
            Betfair client.
        """
        try:
            logger.info(f'Connect to betfair user: {self.config_broker["USERNAME_BETFAIR"]}')
            certs_path = join(BASE_DIR, 'certs')
            aus = False
            client = Api(certs_path, aus=aus, ssl_prefix=self.config_broker["USERNAME_BETFAIR"])
            client.app_key = self.config_broker["APP_KEYS_BETFAIR"]
            # login to betfair api-ng
            resp = client.login(self.config_broker["USERNAME_BETFAIR"], self.config_broker["PASSWORD_BETFAIR"])
            if resp == 'SUCCESS':
                return client
            else:
                logger.error(f'Betfair connection failure by user: {self.config_broker["USERNAME_BETFAIR"]}')
                raise Exception(str(resp))

        except Exception as e:
            logger.exception(f'Betfair connection failure, excepcion: {e}')

    def send_order(self, bet: dataclasses.dataclass) -> None:
        """Send order.

        Parameters
        ----------
        bet: event bet
        """

        logger.info(f'Bet received: {bet.match_name}')
        bet_info = bet.bet_prepare()
        msg = 'PLACING %d BETS...\n' % len(bet_info)
        msg += '%s' % bet_info
        print(msg)
        resp = self.client.place_bets(bet.ticker_id, bet_info)
        print(resp)
        if type(resp) is dict and 'status' in resp:
            if resp['status'] == 'SUCCESS':
                # updated bets field
                bet.bet_id = resp['instructionReports'][0]['betId']
                logger.info(f'Bet placed correctly: {bet.match_name} with betiId: {bet.bet_id}')
                if resp['instructionReports'][0]['sizeMatched'] == bet.quantity:
                    bet.quantity_execute = bet.quantity
                    bet.quantity_left = 0
                else:
                    bet.quantity_execute = float(resp['instructionReports'][0]['sizeMatched'])
                    bet.quantity_left = bet.quantity - bet.quantity_execute
                bet_failed = False
            else:
                bet_failed = True
        else:
            bet_failed = True
        # raise error if bet placement failed
        if bet_failed:
            logger.info(f'Bet NO placed: {bet.match_name}')
            bet.status = 'Failed'
            bet.quantity_execute = 0
            bet.quantity_left = bet.quantity

        elif not bet_failed:  # the bet is good
            if bet.quantity_execute < bet.quantity:
                # pending bets
                bet.status = 'Pending'
                logger.info(f'Bet Pending: {bet.match_name} with betiId: {bet.bet_id}')
                print('BET NO COMPLETED :')
                try:
                    self._manage_pending_bet(bet)

                except Exception as e:
                    logger.error(f'Error manage pending bet in {bet.match_name} with betiId: {bet.bet_id}')
                    print('Fail to cancel bet ' + e)

            else:
                # completed bets
                logger.info(f'Bet Completed: {bet.match_name} with betiId: {bet.bet_id}')
                bet.status = 'Completed'
                print('BET COMPLETED :' + str(bet))
                bet.filled_price = float(resp['instructionReports'][0]['averagePriceMatched'])

        print(bet)

    def _manage_pending_bet(self, bet):
        """
        launch a thread to manage the pending bet
        :param bet:
        :return:
        """

        def run_pending_bets(_bet):
            """
            Run pending bet
            :return:
            """
            print('Manage this pending bet: '+_bet)
            sleep(_bet.cancel_seconds)
            no_found = True
            disc_mens = {'betId': []}
            for currentOrder in self.get_current_bets():
                if len(currentOrder) > 0:
                    disc_mens['betId'].append(currentOrder['betId'])
                    if currentOrder['betId'] == _bet.bet_id:
                        no_found = False
                        _bet.quantity_execute = currentOrder['sizeMatched']
                        # if it has not been executed after x minutes we cancel
                        if _bet.quantity > _bet.quantity_execute:  # cancel
                            _bet.quantity_left = _bet.quantity - _bet.quantity_execute
                            self.cancel_bet(_bet)
                        else:  # if it executed
                            logger.info(f'Bet Completed: {_bet.match_name} with betiId: {_bet.bet_id}')
                            print('BETS COMPLETED IN' + str(_bet.cancel_seconds) + ' SECONDS')
                            _bet.quantity_left = 0
                            _bet.filled_price = float(currentOrder['averagePriceMatched'])

            if no_found:
                try:
                    bets_market_id = self.get_settled_bets(init_datetime=datetime.now() - timedelta(days=1))
                    for bet_settled in bets_market_id:
                        if bet_settled['betId'] == _bet.bet_id:
                            _bet.quantity_execute = _bet.quantity
                            _bet.quantity_left = 0
                            print('BETS COMPLETED IN' + str(_bet.cancel_seconds) + ' SECONDS')
                            logger.info(f'Bet Completed: {_bet.match_name} with betiId: {_bet.bet_id}')
                            _bet.filled_price = float(bet_settled['priceMatched'])
                            no_found = False

                except Exception as e:
                    print('Error to get_settled_bets_market_id')
                    logger.error(f'Error get settled betd in {_bet.match_name} with betiId: {_bet.bet_id}')

            if no_found:
                logger.info(f'Bet dont found: {_bet.match_name} with betiId: {_bet.bet_id}')
                msg = 'manage_pending_bet dont match ' + str(_bet.bet_id) + ' :' + str(disc_mens)
                print(msg)

        t = threading.Thread(target=run_pending_bets, args=(bet,))
        t.daemon = True
        t.start()

    def get_current_bets(self):
        """
        get current bets
        :return:
            list of currents bets
        """

        _datetime = datetime.now()
        resp = self.client.get_current_bets()
        list_result = []
        if type(resp) is dict and 'result' in resp:
            if len(resp['result']['currentOrders']) > 0:
                for result in resp['result']['currentOrders']:
                    price_size = result['priceSize'].copy()
                    result.pop("priceSize", None)
                    result.update(price_size)
                    try:
                        result['matched_date'] = datetime.strptime(result['matchedDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
                    except:
                        result['matched_date'] = _datetime
                    result['placed_date'] = datetime.strptime(result['placedDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
                    result['date_time'] = _datetime
                    list_result.append(result)
        else:
            print('Fail get_current_bets' + str(resp))
            logger.error('Fail get_current_bets')
        return list_result

    def get_settled_bets(self, init_datetime=datetime(2022, 8, 1), end_datetime=datetime.now(), req_id=1):
        """
        get settled bets
        :param init_datetime:
        :param end_datetime:
        :param req_id: by default is 1
        :return:
            list of settled bets between 2 two dates
        """

        maximum = end_datetime
        any_bets = True
        list_result = []
        while any_bets:
            minimum = maximum - timedelta(days=5)
            if init_datetime >= minimum:
                minimum = init_datetime
                any_bets = False
            print('downloading from : ' + str(minimum) + 'to : ' + str(maximum))
            resp = self.client.get_settled_bets(group_by='BET', req_id=req_id, fecha_inicial=minimum,
                                                fecha_final=maximum)

            if type(resp) is dict and 'clearedOrders' in resp:
                if len(resp['clearedOrders']) == 0:
                    break
                for cleared_order in resp['clearedOrders']:
                    item_description = cleared_order['itemDescription'].copy()
                    cleared_order.pop("itemDescription", None)
                    cleared_order.update(item_description)
                    cleared_order['placed_date'] = datetime.strptime(cleared_order['placedDate'],
                                                                     "%Y-%m-%dT%H:%M:%S.%fZ")
                    cleared_order['settled_date'] = datetime.strptime(cleared_order['settledDate'],
                                                                      "%Y-%m-%dT%H:%M:%S.%fZ")
                    cleared_order['market_start_time'] = datetime.strptime(cleared_order['marketStartTime'],
                                                                           "%Y-%m-%dT%H:%M:%S.%fZ")
                    cleared_order['last_matched_date'] = datetime.strptime(cleared_order['lastMatchedDate'],
                                                                           "%Y-%m-%dT%H:%M:%S.%fZ")
                    if cleared_order['placed_date'] < maximum:
                        maximum = cleared_order['placed_date']
                    list_result.append(cleared_order)
            else:
                logger.error('Fail get_settled_bets')
                print('Fail get_settled_bets' + str(resp))
        return list_result

    def cancel_bet(self, bet):
        """Cancel bet.

        Parameters
        ----------
        bet: event bet
        """

        bet_failed = False
        try:
            logger.info(f'Cancel bet in {bet.match_name} with betiId {bet.bet_id}')
            resp = self.client.cancelOrders(betId=bet.bet_id, market_id=bet.ticker_id)
            print('Canceling bet' + 'bet_id: ' + str(bet.bet_id) +
                  'event_id' + str(bet.ticker_id))

        except Exception as e:
            print(e)
            logger.error(f'Error Cancel bet in {bet.match_name} with betiId {bet.bet_id} error: {e}')

        if type(resp) is dict and 'status' in resp:
            if resp['status'] == 'SUCCESS':
                print('BET CANCEL:' + str(bet))

            else:
                bet_failed = True
        else:
            bet_failed = True
        # raise error if bet placement failed
        if bet_failed:
            print('cancelOrders error')
            logger.error(f'Error Cancel bet in {bet.match_name} with betiId {bet.bet_id}')
            print(resp)

    def get_account_details(self) -> Dict:
        """ get details from account"""
        try:
            return self.client.get_account_details()

        except Exception as e:
            logger.error(f'Error get_account_details {e}')

    def get_account_funds(self) -> Dict:
        """ get balance from account"""
        try:
            return self.client.get_account_funds()
        except Exception as e:
            logger.error(f'Error get_account_funds {e}')

    def get_events(self):
        """ get live events and next events"""

        ticker = []
        live = [True, False]
        minutes = self.settings_real_time['minutes']
        for li in live:
            params = _get_parameters(self.settings_real_time, minutes, li)
            for param in params:
                # get events from params
                try:
                    ticker.extend(self.client.get_markets(param))
                    sleep(0.1)
                except Exception as e:
                    logger.error(f'Error get_events {e}')
            names = []
            if len(ticker) > 0:
                if li:
                    print(str(len(ticker)) + ' selections in live')
                else:
                    print(str(len(ticker)) + ' selections in ' + str(minutes))
                # filter markets
                for market in ticker:
                    names.append(market['event']['name'].lower())
                    self.next_events[market['marketId']] = market
                    if market['totalMatched'] < self.settings_real_time['min_total_matched']:
                        # not enough money has been matched, delete this market
                        self.next_events.pop(market['marketId'])
                print(np.unique(names))
            else:
                print('without selections in the next : ' + str(minutes))

    def get_market_books(self, ticker_ids: list):
        """returns a list of prices for given ticker_ids
        """

        # price_data = ['EX_BEST_OFFERS']  # top 3 prices as shown on website
        def _get_market_books(_ticker_id, result):
            result.extend(self.client.get_market_books(_ticker_id, ['EX_BEST_OFFERS']))

        # if there are more than 25 events , we divide into several parts
        if len(ticker_ids) > 25:
            parts = int(np.ceil(len(ticker_ids) / 25))
        else:
            parts = 1

        market_books = []
        threads = []
        for _ticker_id in _chunkit(ticker_ids, parts):
            threads.append(pool.submit(_get_market_books, _ticker_id, market_books))

        wait(threads)

        if len(market_books) == 0:
            logger.error('Error get_market_books')
            print('error en get_market_books : ' + str(market_books))

        return market_books

    def _check_new_data_books(self, ticker_id, selection_id, latest_taken):
        """check if the data is new"""

        try:
            dtime = latest_taken
            self.ultimo_datetime.setdefault(ticker_id, {})
            try:
                self.ultimo_datetime[ticker_id][selection_id]
            except:
                self.ultimo_datetime[ticker_id][selection_id] = dtime
                return True

            if dtime > self.ultimo_datetime[ticker_id][selection_id]:
                self.ultimo_datetime[ticker_id][selection_id] = dtime  # actualizamos
                return True
            else:
                return False
        except:
            return True

    @staticmethod
    def _is_valid(odds_back: list, odds_lay: list, volume_matched: float, last_row: int):
        """Check is the row is valid"""

        # if odds_back, odds_lay and volume_matched have info is valid the data row
        if len(odds_back) > 0 and len(odds_lay) > 0 and volume_matched is not None:
            return True
        if last_row == 1:
            return True

        return False

    def _save_dt_actual_off(self, odd):
        """Save actual off"""

        # Save dt_actual_off to use this info in all selections of the same match
        key = odd.match_name
        if key not in self.data_actual_off:  # if we don't have the match saved
            print('Saving new match: ' + key)
            delete_from = (datetime.today() - timedelta(days=4)).timestamp()
            self.data_actual_off['datetime_real_off'][key] = odd.datetime_scheduled_off.timestamp()
            self.data_actual_off['start'][key] = odd.in_play
            # We delete matchs older than two days to avoid a very large file
            for match in list(self.data_actual_off['datetime_real_off']):
                if self.data_actual_off['datetime_real_off'][match] <= delete_from:
                    self.data_actual_off['datetime_real_off'].pop(match)
                    self.data_actual_off['start'].pop(match)
            with open(file_real_actual_off, 'w') as f:  # saving in json
                json.dump(self.data_actual_off, f)
        elif odd.in_play:  # if we have the match and is in play
            if not self.data_actual_off['start'][key]:  # not in play
                print('Starting match: ' + key)
                if odd.datetime >= odd.datetime_scheduled_off:
                    self.data_actual_off['datetime_real_off'][key] = odd.datetime.timestamp()
                else:
                    self.data_actual_off['datetime_real_off'][key] = odd.datetime_scheduled_off.timestamp()
                self.data_actual_off['start'][key] = odd.in_play
                with open(file_real_actual_off, 'w') as f:  # saving updated info in json
                    json.dump(self.data_actual_off, f)
        return self.data_actual_off['datetime_real_off'][key]

    def processing_data(self, books: list):
        """Processing data and create events odds with the info"""

        books = {i['marketId']: i for i in books}
        matchs = self.next_events  # markets
        in_play = False
        list_delete = []
        # each ticker
        for ticker_id in matchs.keys():
            if ticker_id in books:
                book_event_id = books[ticker_id]  # check book by ticker_id
                match_event_id = matchs[ticker_id]

                # do data for selection inside event data
                for i, runner in enumerate(matchs[ticker_id][u'runners']):
                    # check selection_id
                    selection_id = runner[u'selectionId']
                    # Create odd event for filling
                    odd = Odds()

                    runner_info = list(filter(lambda d: d['selectionId'] == selection_id, book_event_id[u'runners']))
                    # check if we have information from the ticker
                    if len(runner_info) == 0:
                        continue
                    else:
                        runner_info = runner_info[0]
                    if 'lastMatchTime' in book_event_id:
                        latest_taken = pd.to_datetime(book_event_id['lastMatchTime'])
                    else:
                        latest_taken = None
                    # check if this ticker is in play
                    if in_play is False and book_event_id['inplay']:
                        in_play = True
                    # check if data is new
                    if self._check_new_data_books(ticker_id, selection_id, latest_taken):
                        # fill in the dataclass odds
                        odd.datatime_latest_taken = latest_taken
                        odd.selection_id = selection_id
                        odd.selection = runner['runnerName'].lower()
                        odd.player_name = odd.selection
                        odd.ticker_id = ticker_id
                        odd.ticker = match_event_id[u'marketName'].lower()
                        odd.datetime_scheduled_off = pd.to_datetime(matchs[ticker_id]['marketStartTime'])
                        yyyymmdd = odd.datetime_scheduled_off.year * 10000 + odd.datetime_scheduled_off.month * 100 + \
                                   odd.datetime_scheduled_off.day
                        odd.datetime = datetime.utcnow()  # utc
                        odd.match_name = match_event_id['event']['name'].lower()
                        odd.full_description = odd.match_name + '_' + str(yyyymmdd)
                        if 'competition' in match_event_id:
                            odd.competition = match_event_id['competition']['name']
                            odd.competition_id = match_event_id['competition']['id']
                        else:
                            odd.competition = ''
                            odd.competition_id = 0

                        odd.status = book_event_id['status'].lower()  # status of ticker
                        odd.volume_matched = float(book_event_id['totalMatched'])
                        if odd.ticker == 'moneyline':  # for basket
                            odd.ticker = 'match odd'

                        odd.sports_id = int(match_event_id['eventType']['id'])
                        if 'lastPriceTraded' in runner_info:
                            odd.odds_last_traded = float(runner_info['lastPriceTraded'])

                        odd.number_of_active_runners = book_event_id['numberOfActiveRunners']
                        odd.number_of_winners = book_event_id['numberOfWinners']
                        odd.sortPriority = runner['sortPriority']
                        odd.status_selection = runner_info['status'].lower()
                        if 'totalMatched' in runner_info:
                            odd.volume_matched_selection = float(runner_info['totalMatched'])

                        # create a unique field for ticker
                        unico_event_selec = int(ticker_id.replace('.', '')) + int(selection_id)
                        odd.unique_id_match = float(unico_event_selec * 100000000 + yyyymmdd)

                        # change of selections name in the next cases: 'match odds', 'half time',
                        # 'moneyline', 'draw no bet'
                        if odd.ticker in ['match odds', 'half time', 'moneyline', 'draw no bet']:
                            if i == 0:
                                odd.selection = 'home'
                            elif i == 1:
                                odd.selection = 'away'
                            elif i == 2:
                                odd.selection = 'draw'
                        odd.in_play = in_play

                        # if the ticker is over, we add win_flag and put last_row = 1
                        if runner_info['status'] == 'LOSER' and book_event_id['status'] == 'CLOSED':
                            odd.win_flag = 0
                            odd.last_row = 1

                        elif runner_info['status'] == 'WINNER' \
                                and book_event_id['status'] == 'CLOSED':
                            odd.win_flag = 1
                            odd.last_row = 1
                        else:
                            odd.win_flag = 0
                            odd.last_row = 0

                        # if the ticker is over we delete to next_events####
                        if odd.last_row == 1 and book_event_id['status'] == 'CLOSED':
                            list_delete.append(odd.ticker_id)

                        # FILL IN odds
                        odds_back = []
                        size_back = []
                        odds_lay = []
                        size_lay = []
                        # one or more back data available
                        if len(runner_info['ex']['availableToBack']) >= 1:
                            odds_back.append(runner_info['ex']['availableToBack'][0]['price'])
                            size_back.append(runner_info['ex']['availableToBack'][0]['size'])
                        # two or more back data available
                        if len(runner_info['ex']['availableToBack']) >= 2:
                            odds_back.append(runner_info['ex']['availableToBack'][1]['price'])
                            size_back.append(runner_info['ex']['availableToBack'][1]['size'])
                        # three or more back data available
                        if len(runner_info['ex']['availableToBack']) >= 3:
                            odds_back.append(runner_info['ex']['availableToBack'][2]['price'])
                            size_back.append(runner_info['ex']['availableToBack'][2]['size'])

                        odd.odds_back = odds_back
                        odd.size_back = size_back
                        # one or more lay data available
                        if len(runner_info['ex']['availableToLay']) >= 1:
                            odds_lay.append(runner_info['ex']['availableToLay'][0]['price'])
                            size_lay.append(runner_info['ex']['availableToLay'][0]['size'])
                        # two or more lay data available
                        if len(runner_info['ex']['availableToLay']) >= 2:
                            odds_lay.append(runner_info['ex']['availableToLay'][1]['price'])
                            size_lay.append(runner_info['ex']['availableToLay'][1]['size'])
                        # three or more lay data available
                        if len(runner_info['ex']['availableToLay']) >= 3:
                            odds_lay.append(runner_info['ex']['availableToLay'][2]['price'])
                            size_lay.append(runner_info['ex']['availableToLay'][2]['size'])

                        odd.odds_lay = odds_lay
                        odd.size_lay = size_lay
                        # check if the data row is valid
                        if self._is_valid(odds_back, odds_lay, odd.volume_matched, odd.last_row):
                            # Find local team and away team
                            try:
                                local_team = str(odd.match_name.split(' v ')[0])
                                if len(odd.match_name.split(' v ')) == 1:
                                    local_team = str(odd.match_name.split(' @ ')[-1])
                                away_team = str(odd.match_name.split(' v ')[-1])
                                if len(odd.match_name.split(' v ')) == 1:
                                    away_team = str(odd.match_name.split(' @ ')[0])
                            except:
                                local_team = None
                                away_team = None
                            odd.local_team = local_team
                            odd.away_team = away_team
                            sports_id_event = str(int(odd.sports_id)) + '_' + odd.ticker + '_' + str(odd.selection_id)
                            odd.unique_id_ticker = sports_id_event + '_' + str(yyyymmdd)
                            # unique name for ticker and match, for example: albacete vs betis_1_over/under 2.5 goals_202201010820
                            odd.unique_name = odd.match_name + '_' + odd.unique_id_ticker
                            odd.datetime_real_off = pd.to_datetime(self._save_dt_actual_off(odd), unit='s')
                            self.callback_real_time(odd)

        if len(list_delete) > 0:
            for delete in np.unique(list_delete):
                self.next_events.pop(delete)
        return in_play


def get_realtime_data(settings: dict, callback: callable = _callable, config_broker = {}) -> None:
    """Return realtime data for a list of tickers (Events). [Source: Betfair]

    Parameters
    ----------
    settings: dict
        Parameters to get info
    callback: callable (data: Dict) -> None

    """

    trading = Trading(settings_real_time=settings, callback_real_time=callback, config_broker=config_broker)
    total = 100000
    sum_seg = 0
    # if session is True
    session = True
    while session:
        total += settings['time_books_not_play']
        time_books = settings['time_books_not_play']
        if total >= settings['time_events']:
            total = 0
            # Search live events and next events
            trading.get_events()

        # list of ticker ids
        next_events = trading.next_events
        ticker_ids = list(next_events.keys())
        if len(ticker_ids) > 0:
            # get books from markets ids
            market_books = trading.get_market_books(ticker_ids)
            # get the next data
            if len(market_books) > 0:
                process_data = trading.processing_data(market_books)
                if process_data:
                    time_books = settings['time_books_play']  # if there are live events
            sum_seg += time_books
            print(sum_seg)
        sleep(time_books)