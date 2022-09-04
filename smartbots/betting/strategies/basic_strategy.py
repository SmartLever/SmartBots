""" Basic strategic for testing purposes, Back and Lay at entry time """
from dataclasses import dataclass
from smartbots.events import Bet


class Basic_Strategy(object):
    def __init__(self, parameters: dict = None, id_strategy: int = None,
                 callback: callable = None, set_basic: bool = True):
        if callback is None:
            self.callback = self._callback_default
        else:
            self.callback = callback
        self.parameters = parameters
        self.ticker = parameters['ticker']
        self.selection = parameters['selection']
        self.action = parameters['action']  # action
        self.quantity = parameters['quantity']  # quantity
        self.init_odd = parameters['init_odd']  # init_odd
        self.end_odd = parameters['end_odd']  # end_odd
        self.init_time = parameters['init_time']  # init_time
        self.end_time = parameters['end_time']  # end_time
        self.id_strategy = id_strategy
        # Parameters for unique events
        self.n_events = {}  # dict with unique as key and number of events as value
        self.unique_control = {}  # dict with unique as key and true or false as value
        if set_basic:
            self.add_odds

    def _callback_default(self, event_bet: dataclass):
        """ callback for Bet by defalt """

    def _fill_unique_data(self, unique: str):
        """ Fill the unique data for event type"""
        self.unique_control[unique] = True
        self.n_events[unique] = 0

    def _time_conditions(self, odds: dataclass):
        """ Check if the event is between the times parameters"""
        from_init = (odds.datatime_latest_taken - odds.datetime_real_off).seconds / 60
        # check range time
        if self.init_time <= from_init <= self.end_time:
            return True
        return False

    def check_control_unique(self, unique: str):
        """ Check if the event is unique """
        if unique not in self.unique_control:
            self.unique_control[unique] = True
            self._fill_unique_data(unique)
            return True
        else:
            return False

    def add_odds(self, odds: dataclass):
        """ Add event to the strategy and apply logic """
        if odds.selection == self.selection:
            unique = odds.unique_name
            self.check_control_unique(unique)
            if self.n_events[unique] == 0:
                # check is the odds_last_traded has value
                if odds.odds_last_traded is not None:
                    if self._time_conditions(odds):
                        # check is the odds_last_traded is between the odds parameters
                        if self.end_odd >= odds.odds_last_traded >= self.init_odd:

                            # just one bet for event
                            self.n_events[unique] += 1
                            bet = Bet(datetime=odds.datetime, dtime_zone=odds.dtime_zone, ticker=self.ticker,
                                      selection=odds.selection, odds=odds.odds_last_traded, quantity=self.quantity,
                                      match_name=odds.match_name, ticker_id=odds.ticker_id, selection_id=odds.selection_id,
                                      action=self.action
                                      )

                            self.callback(bet)  # send bet to betting platform
