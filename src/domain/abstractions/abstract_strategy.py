from abc import ABC
from dataclasses import dataclass
from src.domain.events import Order, Bet
import datetime as dt
from src.domain.equity_handler import Equity


def _callback_default(event_order: dataclass):
    """ callback for Order by defalt """
    print(event_order)


class Abstract_Strategy(ABC):
    """ Abstract class for Strategy
    All strategies must inherit from this class"""
    def __init__(self, parameters: dict = None, id_strategy: int = None,
                 callback: callable = None, set_basic: bool = True):
        if callback is None:
            self.callback = _callback_default
        else:
            self.callback = callback
        self.parameters = parameters
        if 'limit_save_values' in self.parameters:
            self.limit_save_values = self.parameters['limit_save_values']
        else:
            self.limit_save_values = 0
        self.ticker = parameters['ticker']
        if 'tickers_to_feeder' not in self.parameters:
            self.tickers_to_feeder = self.ticker  # tickers for feed the strategy by events, default is ticker
        if 'ticker_broker' in self.parameters:
            self.ticker_broker = self.parameters['ticker_broker']
        self.quantity = parameters['quantity']
        self.contracts = 0  # number of contract in the position
        self.id_strategy = id_strategy
        self.type_trading = 'financial' # by default
        self.n_events = 0  # number of events received
        self.n_orders = 0  # number of orders sent
        self.position = 0  # position in the strategy, 1 Long, -1 Short, 0 None
        self.inicial_values = False  # Flag to set inicial values
        self.saves_values = {'datetime': [], 'position': [], 'close': []}
        # Equity handler of the strategy
        if 'save_equity_vector_for' in self.parameters:
            self.save_equity_vector_for = self.parameters['save_equity_vector_for']
        else:
            self.save_equity_vector_for = ['close_day', 'order']
        self.bar_to_equity = False
        if 'bar' in self.save_equity_vector_for:
            self.bar_to_equity = True
        if 'name' not in self.parameters:
            self.name = 'strategy'
        else:
            self.name = self.parameters['name']

        fees = 0
        if 'fees' in self.parameters:
            fees = self.parameters['fees']
        slippage = 0
        if 'slippage' in self.parameters:
            slippage = self.parameters['slippage']
        point_value = 1
        if 'point_value' in self.parameters:
            point_value = self.parameters['point_value']
        if 'base_currency' in self.parameters:
            base_currency = self.parameters['base_currency']
        else:
            base_currency = {'ticker': 'USD', 'value': 1}  # default base currency if the product is in USD already

        self.equity_hander_estrategy = Equity(ticker=self.ticker, asset_type='crypto', fees=fees, slippage=slippage,
                                              point_value=point_value, id_strategy=self.id_strategy,
                                              base_currency=base_currency)

        if set_basic:
            self.add_bar = self._add_event_example

    def update_equity(self, event: dataclass):
        """ Update equity """
        is_day_closed = False
        if event.event_type == 'bar':
            update = {'quantity': 0, 'price': event.close, 'datetime': event.datetime}
        elif event.event_type == 'order':
            quantity = event.quantity
            if event.action == 'sell':
                quantity = -quantity
            update = {'quantity': quantity, 'price': event.price, 'datetime': event.datetime}
        elif event.event_type == 'tick' and event.tick_type == 'close_day':
            update = {'quantity': 0, 'price': event.price, 'datetime': event.datetime}
            is_day_closed = True
        # update equity
        self.equity_hander_estrategy.update(update)
        self.equity_hander_estrategy.fill_equity_vector()
        # update equity day
        if is_day_closed:
            self.equity_hander_estrategy.fill_equity_day()

    def get_order_id_sender(self):
        """ Return order_id_sender """
        return f'{self.id_strategy}_{self.n_orders}_{dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")}'

    def send_order(self, price=None, quantity=None, action=None, ticker=None, type='market', datetime=None,
                   match_name=None, ticker_id=None, selection_id=None, cancel_seconds=None, unique_name=None,
                   selection=None):
        """ Send order to exchange or broker """
        if self.type_trading in ['financial', 'crypto']:
            # contract tracking
            if action == 'buy':
                self.contracts += quantity
            elif action == 'sell':
                self.contracts -= quantity
            # update position tracking
            if self.contracts < 0:
                self.position = -1
            elif self.contracts > 0:
                self.position = 1
            elif self.contracts == 0:
                self.position = 0

            sender_id = self.get_order_id_sender()
            order_id_sender = self.get_order_id_sender()
            order = Order(datetime=datetime,
                          dtime_zone='UTC', ticker=ticker, action=action,
                          price=price, quantity=quantity, type=type, sender_id=sender_id,
                          order_id_sender=order_id_sender)
            self.callback(order)
            self.n_orders += 1
            if self.limit_save_values > 0:  # save values by limit, this way it is more efficient
                if len(self.saves_values['datetime']) > self.limit_save_values:
                    for k in self.saves_values.keys():
                        self.saves_values[k] = self.saves_values[k][-self.limit_save_values:]
            # update equity
            self.update_equity(order)

        elif self.type_trading == 'betting':
            bet = Bet(datetime=datetime, dtime_zone='UTC', ticker=ticker,
                      selection=selection, odds=price, quantity=quantity,
                      match_name=match_name, ticker_id=ticker_id,
                      selection_id=selection_id, action=action,
                      cancel_seconds=cancel_seconds, unique_name=unique_name
                      )

            self.callback(bet)  # send bet to betting platform

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
                                action=self.parameters['inicial_action'], type='market', datetime=event.datetime)
                # Change action
                if self.parameters['inicial_action'] == 'buy':
                    self.parameters['inicial_action'] = 'sell'
                elif self.parameters['inicial_action'] == 'sell':
                    self.parameters['inicial_action'] = 'buy'
            # save values
            self.saves_values['datetime'].append(event.datetime)
            self.saves_values['position'].append(self.position)
            self.saves_values['close'].append(event.close)

        else:
            pass

