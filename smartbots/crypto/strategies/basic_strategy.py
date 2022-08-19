""" Basic strategic for testing purposes, buy and sell at entry time """
import time
from dataclasses import dataclass
from smartbots.events import Order
import datetime as dt


class Basic_Strategy(object):
    def __init__(self, parameters: dict = None, id_strategy: int=None,
                 callback: callable=None, set_basic: bool= True):
        if callback is None:
            self.callback = self._callback_default
        else:
            self.callback = callback
        self.parameters = parameters
        self.ticker = parameters['ticker']
        self.id_strategy = id_strategy
        self.n_events = 0 # number of events received
        self.n_orders = 0 # number of orders sent
        if set_basic:
            self.add_bar = self._add_bar_example


    def _callback_default(self, event_order: dataclass):
        """ callback for Order by defalt """
        print(event_order)

    def get_order_id_sender(self):
        """ Return order_id_sender """
        return f'{self.id_strategy}_{self.n_orders}_{dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")}'

    def send_order(self,price=None, quantity=None, action=None, ticker=None,type='market'):
        """ Send order to exchange or broker """

        sender_id = self.get_order_id_sender()
        order_id_sender = self.get_order_id_sender()
        order = Order(datetime=dt.datetime.utcnow(),
                      dtime_zone='UTC', ticker=ticker, action=action,
                      price=price, quantity=quantity, type=type, sender_id=sender_id,
                      order_id_sender=order_id_sender)
        self.callback(order)
        self.n_orders += 1

    def add_bar(self, bar: dataclass):
        """ Add event to the strategy and apply logic """
        pass


    def _add_bar_example(self, bar: dataclass):
        """ Basic logic for testing purposes """
        self.n_events += 1
        if self.n_events % self.parameters['entry'] == 0:
            self.send_order(ticker = bar.ticker, price=bar.close, quantity=self.parameters['quantity'],
                            action= self.parameters['inicial_action'], type='market')
            # Chamge action
            if self.parameters['inicial_action'] == 'buy':
                self.parameters['inicial_action']  = 'sell'
            elif self.parameters['inicial_action']  == 'sell':
                self.parameters['inicial_action']  = 'buy'

