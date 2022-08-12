""" Basic strategic for testing purposes, buy and sell at entry time """
import time
from dataclasses import dataclass
from smartbots.events import Order


class Basic_Strategy(object):
    def __init__(self, parameters: dict = None, id_strategy:int=None,
                 callback: callable=None):
        if callback is None:
            self.callback = self._callback_default
        else:
            self.callback = callback
        self.parameters = parameters
        self.ticker = parameters['ticker']
        self.id_strategy = id_strategy
        self.entry = parameters['entry']
        self.n_events = 0 # number of events received
        self.action = parameters['inicial_action']
        self.quantity = parameters['quantity']

    def _callback_default(self, event_order: dataclass):
        """ callback for Order by defalt """
        print(event_order)

    def add_bar(self, bar: dataclass):
        """ Add event to the strategy and apply logic """
        self.n_events += 1
        if self.n_events % self.entry == 0:
            order = Order(datetime=bar.datetime,
                          dtime_zone=bar.dtime_zone, ticker=self.ticker,action=self.action,
                          price=bar.close, quantity=self.quantity)
            self.callback(order) # send order to exchange or broker
            # Chamge action
            if self.action == 'buy':
                self.action = 'sell'
            elif self.action == 'sell':
                self.action = 'buy'

