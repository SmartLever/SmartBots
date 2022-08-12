""" Basic strategic for testing purposes, Back and Lay at entry time """
import time
from dataclasses import dataclass
from smartbots.events import Bet


class Basic_Strategy(object):
    def __init__(self, parameters: dict = None, id_strategy:int=None,
                 callback: callable=None):
        if callback is None:
            self.callback = self._callback_default
        else:
            self.callback = callback
        self.parameters = parameters
        self.ticker = parameters['ticker']
        self.selecion = parameters['selection']
        self.id_strategy = id_strategy
        self.entry = parameters['entry']
        # Parameters for unique events
        self.n_events = {} # dict with unique as key and number of events as value
        self.action = {}# dict with unique as key and action as value
        self.quantity = {} # dict with unique as key and quantity as value
        self.unique_control = {} # dict with unique as key and true or false as value

    def _callback_default(self, event_bet: dataclass):
        """ callback for Bet by defalt """
        print(event_bet)

    def _fill_unique_data(self, unique: str):
        """ Fill the unique data for event type"""
        self.unique_control[unique] = True
        self.quantity[unique] = self.parameters['quantity']
        self.action[unique] = self.parameters['inicial_action']
        self.n_events[unique] = 0

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
        unique = odds.unique_name
        self.check_control_unique(unique)
        self.n_events[unique] += 1
        if self.n_events[odds.unique_name] % self.entry == 0:
            bet = Bet(datetime=odds.datetime, datetime_epoch=odds.datetime_epoch,
                          dtime_zone=odds.dtime_zone, ticker=self.ticker,selection=self.selection,
                          odds=odds.odds, quantity=self.quantity,match_name=odds.match_name)
            self.callback(bet) # send bet to betting platform
            # Change action
            if self.action[unique] == 'back':
                self.action[unique] = 'lay'
            elif self.action[unique] == 'lay':
                self.action[unique] = 'back'

