import importlib
from dataclasses import dataclass
from src.infraestructure.brokerMQ import Emit_Events, receive_events
from src.application.services import data_reader
import datetime as dt
import os
from src.application import conf
import pandas as pd
from src.domain.equity_handler import Equity_Handler
from src.infraestructure.database_handler import Universe
from src.infraestructure.health_handler import Health_Handler
from pathlib import Path


class Portfolio_Constructor(object):
    def __init__(self, conf_portfolio: dict, run_real: bool = False, asset_type: str = None,
                 send_orders_to_broker: bool = False, start_date: dt.datetime = dt.datetime(2022, 1, 1),
                 end_date: dt.datetime = dt.datetime.utcnow(), inicial_cash: float = 0, path_to_strategies: str = None,
                 routing_key: str = 'bar,petition,timer,webhook'):
        """ Run portfolio of strategies"""
        if asset_type is None:
            error_msg = 'asset_type is required'
            raise ValueError(error_msg)
        self.print_events_realtime = False
        self.in_real_time = False
        self.path_to_strategies = path_to_strategies # path to strategies, default is None
        self.start_date = start_date
        self.end_date = end_date
        self.conf_portfolio = conf_portfolio
        self.name = conf_portfolio['Name']
        self.data_sources = conf_portfolio['Data_Sources']
        self.run_real = run_real
        self.asset_type = asset_type
        self.ticker_to_strategies = {}  # fill with function load_strategies_conf()
        self.ticker_to_id_strategies = {}
        self.total_strategies_with_timer = []
        self._load_strategies_conf()
        self.send_orders_to_broker = send_orders_to_broker
        self.orders = []
        self.bets = []
        self.bets_result = {}  # keys: match unique and values: result
        self.routing_key = routing_key
        # health log
        self.config_brokermq = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
                                'password': conf.RABBITMQ_PASSWORD}
        if self.run_real:
            self.health_handler = Health_Handler(n_check=10,
                                                 name_service=self.name,
                                                 config=self.config_brokermq)
        else:
            self.health_handler = None

        if self.send_orders_to_broker: # if send orders to broker, send orders to brokerMQ
            self.emit_orders = Emit_Events(config=self.config_brokermq)
        # equity handler
        self.equity_handler = Equity_Handler(ticker_to_strategies=self.ticker_to_strategies,
                                             inicial_cash=inicial_cash)


    def _load_strategies_conf(self):
        """ Load the strategies configuration """
        list_stra = {}
        for parameters in self.conf_portfolio['Strategies']:
            strategy_name = parameters['strategy']
            _id = parameters['id']
            ticker = parameters['params']['ticker']
            if 'tickers_to_feeder' in parameters['params']:
                tickers_feeder = parameters['params']['tickers_to_feeder'].split(',')  # set in list
            else:
                tickers_feeder = ticker
            parameters['params']['tickers_feeder'] = tickers_feeder
            set_basic = False
            if strategy_name == 'Basic_Strategy':
                set_basic = True
            if strategy_name not in list_stra:  # import strategy only once
                list_stra[strategy_name] = self._get_strategy(self.asset_type, strategy_name)
            if ticker not in self.ticker_to_strategies:
                self.ticker_to_strategies[ticker] = []
                self.ticker_to_id_strategies[ticker] = []
            for t in tickers_feeder:
                self.ticker_to_strategies[t] = []
                self.ticker_to_id_strategies[t] = []

            strategy_obj = list_stra[strategy_name](parameters['params'], id_strategy=_id,
                                                    callback=self._callback_orders, set_basic = set_basic)

            if hasattr(strategy_obj, 'add_timer'):
                # if the strategy has this method, add timer
                self.total_strategies_with_timer.append(strategy_obj)
            self.ticker_to_strategies[ticker].append(strategy_obj)
            self.ticker_to_id_strategies[ticker].append(_id)
            for t in tickers_feeder: # set strategies to feed with tickers_feeder
                self.ticker_to_strategies[t].append(strategy_obj)
                self.ticker_to_id_strategies[t].append(_id)

    def _get_strategy(self, asset_type: str, strategy_name: str):
        """ Load the strategy dinamically"""
        try:
            # check if exist file with the strategy
            path_to_strategy = os.path.join(conf.path_modulo, 'domain', 'strategies', strategy_name.lower() + '.py')
            if asset_type == 'betting':
                strategy_file = 'strategies_betting'
            else:
                strategy_file = 'strategies'
            name = f'src.domain.{strategy_file}.{strategy_name.lower()}'
            if not os.path.exists(path_to_strategy):
                path_to_strategy = Path(os.path.join(self.path_to_strategies, strategy_name.lower() + '.py'))
                parent = path_to_strategy.parent.parent.name
                # get name last folder

                name = f'my_smartbots.{parent}.strategies.{strategy_name.lower()}'

            elif os.path.exists(path_to_strategy) is False:
                error_msg = f'Error, strategy {strategy_name} not found'
                raise ValueError(error_msg)

            strategy_module = importlib.import_module(name)
            strategy_class = getattr(strategy_module, strategy_name)
            return strategy_class
        except Exception as e:
            raise ValueError(f'Error loading strategy {strategy_name}') from e

    def get_saved_values_strategy(self, id_strategy: int = None):
        # Get saved values for the strategy
        frames = {}
        for t in self.ticker_to_strategies.keys():
            for strategy in self.ticker_to_strategies[t]:
                if id_strategy is None or strategy.id_strategy == id_strategy:
                    df = pd.DataFrame(strategy.get_saved_values())
                    df['ticker'] = t
                    df.set_index('datetime', inplace=True)
                    frames[strategy.id_strategy] = df
        return frames

    def get_saved_values_strategies_last(self):
        # Get last saved values for the strategy
        dict_values = {}
        for t in self.ticker_to_strategies.keys():
            for strategy in self.ticker_to_strategies[t]:
                values = strategy.get_saved_values()
                dict_values[strategy.id_strategy] = {}
                dict_values[strategy.id_strategy]['ticker'] = strategy.ticker
                dict_values[strategy.id_strategy]['close'] = values['close'][-1]
                dict_values[strategy.id_strategy]['position'] = values['position'][-1]
                dict_values[strategy.id_strategy]['quantity'] = strategy.quantity

        return dict_values

    def close_all_positions(self):
        for t in self.ticker_to_strategies.keys():
            for strategy in self.ticker_to_strategies[t]:
                if hasattr(strategy, 'close_all_positions'):
                    strategy.close_all_positions()

    def run(self):
        print(f'running Portfolio {self.name}')
        self.run_simulation()
        if self.run_real:
            self.run_realtime()

    def run_simulation(self):
        """ Run Backtest portfolio"""
        self.in_real_time = False
        if self.data_sources is not None:
            if self.asset_type in ['crypto', 'financial']:
                for event in data_reader.load_tickers_and_create_events(self.data_sources,
                                                                        start_date=self.start_date, end_date=self.end_date):
                    self._callback_datafeed(event)
            elif self.asset_type == 'betting':
                for event in data_reader.load_tickers_and_create_events_betting(self.data_sources,
                                                                                start_date=self.start_date,
                                                                                end_date=self.end_date
                                                                                ):
                    self._callback_datafeed_betting(event)
            else:
                raise ValueError(f'Asset type {self.asset_type} not supported')
        else:
            print('No data sources for backtest')

    def process_petitions(self, event: dataclass):
        """ Recieve a event peticion and get the data from the data source and save it in the DataBase"""
        if event.event_type == 'petition':
            if event.name_portfolio == self.name:
                data_to_save = None
                print(f'Petition {event}')
                if event.function_to_run == 'get_saved_values_strategy':
                    data_to_save = self.get_saved_values_strategy()
                elif event.function_to_run == 'get_saved_values_strategies_last':
                    data_to_save = self.get_saved_values_strategies_last()
                elif event.function_to_run == 'close_all_positions':
                    self.close_all_positions()
                if data_to_save is not None:
                    name_library = event.path_to_saving
                    name = event.name_to_saving
                    store = Universe(host=conf.MONGO_HOST, port=conf.MONGO_PORT)
                    lib = store.get_library(name_library, library_chunk_store=False)
                    lib.write(name, data_to_save)
                    print(f'Save {name} in {name_library}.')

    def run_realtime(self):
        self.print_events_realtime = True
        self.in_real_time = True
        print('running real  of the Portfolio, waitig Events')
        if self.asset_type in ['crypto', 'financial']:
            receive_events(routing_key=self.routing_key, callback=self._callback_datafeed, config=self.config_brokermq)
        elif self.asset_type == 'betting':
            receive_events(routing_key='odds,petition', callback=self._callback_datafeed_betting, config=self.config_brokermq)
        else:
            raise ValueError(f'Asset type {self.asset_type} not supported')

    def _callback_orders(self, order_or_bet: dataclass):
        """ Order event from strategies"""
        order_or_bet.portfolio_name = self.name
        order_or_bet.status = 'from_strategy'
        if self.asset_type == 'crypto' or self.asset_type == 'financial':
            self.orders.append(order_or_bet) # append the order to the list of orders
            if self.in_real_time and self.send_orders_to_broker:
                print(order_or_bet)
                self.emit_orders.publish_event(conf.ROUTING_KEY, order_or_bet)
        elif self.asset_type == 'betting':
            self.bets.append(order_or_bet)
            if self.in_real_time and self.send_orders_to_broker:
                print(order_or_bet)
                self.emit_orders.publish_event('bet', order_or_bet)
        elif self.send_orders_to_broker:
            raise ValueError(f'Asset type {self.asset_type} not supported')

    def _callback_datafeed_betting(self, event: dataclass):
        """ Feed portfolio with data from events for asset type Betting,
         recieve dict with key as topic and value as event"""
        if self.in_real_time:
            self.health_handler.check()
        if event.event_type == 'odds':
            # save result
            if event.last_row == 1:
                self.bets_result[event.unique_name] = event.win_flag
            if self.print_events_realtime:
                print(event)
            try:
                strategies = self.ticker_to_strategies[event.ticker]
            except:
                self.ticker_to_strategies[event.ticker] = []  # default empty list
                strategies = self.ticker_to_strategies[event.ticker]

            for strategy in strategies:
                if event.last_row == 0:
                    strategy.add_event(event)

    def _callback_datafeed(self, event: dataclass):
        """ Feed portfolio with data from events for asset Crypto and Finance,
        recieve  events"""
        if self.in_real_time:
            self.health_handler.check()
        if event.event_type == 'bar':  # bar event, most common.
            if self.print_events_realtime:
                print(f'bar {event.ticker} {event.datetime} {event.close}')
            try:
                strategies = self.ticker_to_strategies[event.ticker]
            except:
                self.ticker_to_strategies[event.ticker] = []  # default empty list
                strategies = self.ticker_to_strategies[event.ticker]
            for strategy in strategies:
                strategy.add_event(event)    
                
        elif event.event_type == 'timer':
            for strategy in self.total_strategies_with_timer:
                strategy.add_timer(event)

        elif event.event_type == 'petition': # petition to get data from the portfolio
            """ If the petition do not work it keeps working"""
            try:
                self.process_petitions(event)
            except Exception as e:
                print(f'Error processing petitions {e}')

        elif event.event_type == 'webhook':
            """ webhook event"""
            try:
                for t in self.ticker_to_strategies.keys():
                    strategies = self.ticker_to_strategies[t]
                    for strategy in strategies:
                        strategy.add_event(event)
            except Exception as e:
                print(f'Error processing webhook {e}')

        elif event.event_type == 'tick' and event.tick_type == 'close_day': # update equity with last price
            if self.print_events_realtime:
                print(f'tick close_day {event.ticker} {event.datetime} {event.price}')
            try:
                strategies = self.ticker_to_strategies[event.ticker]
            except:
                self.ticker_to_strategies[event.ticker] = []  # default empty list
                strategies = self.ticker_to_strategies[event.ticker]
            for strategy in strategies:
                strategy.add_event(event)
            self.equity_handler.calculate_equity_day(event.datetime) # update equity portfolio with close

