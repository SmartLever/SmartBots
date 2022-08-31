""" Basic strategic for testing purposes, buy and sell at entry time """
import time
from dataclasses import dataclass
from smartbots.events import Order
import datetime as dt


class Basic_Strategy(object):
    def __init__(self, parameters: dict = None, id_strategy: int = None,
                 callback: callable = None, set_basic: bool = True):
        if callback is None:
            self.callback = self._callback_default
        else:
            self.callback = callback
        self.parameters = parameters
        if 'limit_save_values' in self.parameters:
            self.limit_save_values = self.parameters['limit_save_values']
        else:
            self.limit_save_values = 0
        self.ticker = parameters['ticker']
        self.quantity = parameters['quantity']
        self.id_strategy = id_strategy
        self.n_events = 0  # number of events received
        self.n_orders = 0  # number of orders sent
        self.position = 0  # position in the strategy, 1 Long, -1 Short, 0 None
        self.inicial_values = False  # Flag to set inicial values
        self.saves_values = {'datetime': [], 'position': [], 'close': []}
        if set_basic:
            self.add_bar = self._add_event_example

    def _callback_default(self, event_order: dataclass):
        """ callback for Order by defalt """
        print(event_order)

    def get_order_id_sender(self):
        """ Return order_id_sender """
        return f'{self.id_strategy}_{self.n_orders}_{dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")}'

    def send_order(self, price=None, quantity=None, action=None, ticker=None, type='market', datetime=None):
        """ Send order to exchange or broker """

        sender_id = self.get_order_id_sender()
        order_id_sender = self.get_order_id_sender()
        order = Order(datetime=datetime,
                      dtime_zone='UTC', ticker=ticker, action=action,
                      price=price, quantity=quantity, type=type, sender_id=sender_id,
                      order_id_sender=order_id_sender)
        self.callback(order)
        self.n_orders += 1
        if self.limit_save_values > 0: # save values by limit, this way it is more efficient
           if len(self.saves_values['datetime']) > self.limit_save_values:
               for k in self.saves_values.keys():
                   self.saves_values[k] = self.saves_values[k][-self.limit_save_values:]

    def add_event(self, event: dataclass):
        """ Add event to the strategy and apply logic """
        pass

    def get_saved_values(self):
        """ Return values saved """
        return self.saves_values

    def _add_event_example(self, event: dataclass):
        """ Basic logic for testing purposes """
        if event.event_type == 'bar':
            self.n_events += 1
            if self.n_events % self.parameters['entry'] == 0:
                self.send_order(ticker=event.ticker, price=event.close, quantity=self.parameters['quantity'],
                                action=self.parameters['inicial_action'], type='market',datetime=event.datetime)
                # Chamge action
                if self.parameters['inicial_action'] == 'buy':
                    self.position = 1
                    self.parameters['inicial_action'] = 'sell'
                elif self.parameters['inicial_action'] == 'sell':
                    self.position = 0
                    self.parameters['inicial_action'] = 'buy'
            # save values
            self.saves_values['datetime'].append(event.datetime)
            self.saves_values['position'].append(self.position)
            self.saves_values['close'].append(event.close)

        else:
            pass
