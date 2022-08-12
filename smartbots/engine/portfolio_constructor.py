import importlib
from dataclasses import dataclass
from smartbots.brokerMQ import Emit_Events, receive_events
from smartbots.engine import data_loader
import datetime as dt

class Portfolio_Constructor(object):
    def __init__(self, conf_portfolio: dict, run_real: bool = False, asset_type: str = None,
                 send_orders_to_broker: bool = False, start_date: dt.datetime =dt.datetime(2022,1,1)
                 , end_date: dt.datetime = dt.datetime.utcnow()):
        """ Run portfolio of strategies"""
        self.print_events_realtime = False
        self.start_date = start_date
        self.end_date = end_date
        if asset_type is None:
            error_msg = 'asset_type is required'
            raise ValueError(error_msg)
        self.conf_portfolio = conf_portfolio
        self.name = conf_portfolio['Name']
        self.data_sources = conf_portfolio['Data_Sources']
        self.run_real = run_real
        self.asset_type = asset_type
        self.ticker_to_strategies = {}  # fill with function load_strategies_conf()
        self._load_strategies_conf()
        self.send_orders_to_broker = send_orders_to_broker
        self.orders = []
        self.bets = []
        if self.send_orders_to_broker:
            self.emit_orders = Emit_Events()

    def _load_strategies_conf(self):
        """ Load the strategies configuration """
        list_stra = {}
        for parameters in self.conf_portfolio['Strategies']:
            strategy_name = parameters['strategy']
            _id = parameters['id']
            ticker = parameters['params']['ticker']
            if strategy_name not in list_stra:  # import strategy only once
                list_stra[strategy_name] = self._get_strategy(self.asset_type, strategy_name)
            if ticker not in self.ticker_to_strategies:
                self.ticker_to_strategies[ticker] = []
            strategy_obj = list_stra[strategy_name](parameters['params'], id_strategy=_id,
                                                    callback=self._callback_orders)
            self.ticker_to_strategies[ticker].append(strategy_obj)

    def _get_strategy(self, asset_type: str, strategy_name: str):
        """ Load the strategy dinamically"""
        try:
            name = f'smartbots.{asset_type}.strategies.{strategy_name.lower()}'
            strategy_module = importlib.import_module(name)
            strategy_class = getattr(strategy_module, strategy_name)
            return strategy_class
        except Exception as e:
            raise ValueError(f'Error loading strategy {strategy_name}') from e

    def run(self):
        print(f'running Portfolio {self.name}')
        self.run_simulation()
        if self.run_real:
            self.print_events_realtime = True
            self.run_realtime()

    def run_simulation(self):
        if self.asset_type == 'crypto':
            for event in data_loader.load_tickers_and_create_events(self.data_sources,
                                                                    start_date=self.start_date, end_date=self.end_date):
                self._callback_datafeed(event)
        elif self.asset_type == 'betting':
            for event in data_loader.load_tickers_and_create_events_betting(self.data_sources):
                self._callback_datafeed_betting(event)
        else:
            raise ValueError(f'Asset type {self.asset_type} not supported')


    def run_realtime(self):
        print('running real  of the Portfolio, waitig Events')
        if self.asset_type == 'crypto':
            receive_events(routing_key='bar', callback=self._callback_datafeed)
        elif self.asset_type == 'betting':
            receive_events(routing_key='odds', callback=self._callback_datafeed_betting)
        else:
            raise ValueError(f'Asset type {self.asset_type} not supported')

    def _callback_orders(self, order_or_bet: dataclass):
        """ Order event from strategies"""
        if self.send_orders_to_broker and self.asset_type == 'crypto':
                self.emit_orders.publish_event('order', order_or_bet)
                print(order_or_bet)
                self.orders.append(order_or_bet)
        elif self.send_orders_to_broker and self.asset_type == 'betting':
            self.emit_orders.publish_event('bet', order_or_bet)
            print(order_or_bet)
            self.bets.append(order_or_bet)
        elif self.send_orders_to_broker:
            raise ValueError(f'Asset type {self.asset_type} not supported')

    def _callback_datafeed_betting(self, event_info: dict):
        """ Feed portfolio with data from events for asset type Betting,
         recieve dict with key as topic and value as event"""
        if 'odds' in event_info:
            odds = event_info['odds']
            if self.print_events_realtime:
                print(odds)
            try:
                strategies = self.ticker_to_strategies[odds.ticker]
            except:
                self.ticker_to_strategies[odds.ticker] = []  # default empty list
                strategies = self.ticker_to_strategies[odds.ticker]

            for strategy in strategies:
                strategy.add_odds(odds)

    def _callback_datafeed(self, event_info: dict):
        """ Feed portfolio with data from events for asset Crypto and Finance,
        recieve dict with key as topic and value as event"""
        if 'bar' in event_info:
            bar = event_info['bar']
            if self.print_events_realtime:
                print(bar)
            try:
                strategies = self.ticker_to_strategies[bar.ticker]
            except:
                self.ticker_to_strategies[bar.ticker] = []  # default empty list
                strategies = self.ticker_to_strategies[bar.ticker]

            for strategy in strategies:
                strategy.add_bar(bar)
