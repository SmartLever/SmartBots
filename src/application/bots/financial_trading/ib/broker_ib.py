""" Recieved events orders from Portfolio and send it to the broker or exchange for execution"""
from src.infrastructure.brokerMQ import Emit_Events
from src.domain.models.positions import Positions
import pytz
from src.application.base_logger import logger
from typing import Dict
from src.application import conf
import datetime as dt
from src.infrastructure.ib.ib_handler import Trading
from src.application.services.health_handler import Health_Handler
from src.infrastructure.database_handler import Universe
from src.domain.models.balance import Balance
import os

class BrokerIB(object):
    """
    Class
    for broker MT4.

    """
    def __init__(self, config_brokermq: Dict = {}, send_orders_status=True, exchange_or_broker='ib', account=''):
        self.config_brokermq = config_brokermq
        self.config_broker = {'HOST_IB': conf.HOST_IB, 'PORT_IB': int(conf.PORT_IB), 'CLIENT_IB': int(conf.CLIENT_IB_BROKER)}
        path_ticker = os.path.join(conf.path_to_principal, 'ticker_info_ib.csv')
        self.trading = Trading(send_orders_status=send_orders_status, exchange_or_broker=f'{exchange_or_broker}_broker',
                               config_broker=self.config_broker, config_brokermq=self.config_brokermq, path_ticker=path_ticker)
        # Log event health of the service
        self.health_handler = Health_Handler(n_check=6,
                                             name_service=f'broker_{exchange_or_broker}',
                                             config=self.config_brokermq)
        self.emit = Emit_Events(config=config_brokermq)
        self.name_portfolio = conf.NAME_FINANCIAL_PORTOFOLIO
        # Create library for saving balances
        name = 'balance'
        # Create connection  to DataBase
        store = Universe(host=conf.MONGO_HOST, port=conf.MONGO_PORT)
        self.lib_balance = store.get_library(name, library_chunk_store=False)
        self.exchange = exchange_or_broker
        self.account = account

    def start_update_orders_status(self):
        self.trading.start_update_orders_status()

    def check_balance(self) -> None:
        try:
            now = dt.datetime.utcnow()
            balance = self.trading.get_total_balance(self.account)
            if balance['value'] is not None:
                logger.info(f'Balance {balance} {dt.datetime.utcnow()} in account {self.account}')
                control_balance = dt.datetime(now.year, now.month, now.day, now.hour, now.minute)
                unique = f'{self.account}_{control_balance.strftime("%Y-%m-%d %H:%M:00")}'
                # saving objective balance
                balance = Balance(datetime=now, balance=balance,
                                  account=self.name_portfolio)

                self.lib_balance.write(unique, balance, metadata={'datetime': now,
                                                                  'account': self.account})
                print(f'Balance {balance} {dt.datetime.utcnow()}')
                self.health_handler.check()
            else:
                logger.error(f'Error Getting {self.exchange} Balance')
                self.health_handler.send(description='error', state=0)
        except Exception as e:
            logger.error(f'Error Getting {self.exchange} Balance: {e}')
            self.health_handler.send(description=e, state=0)

    def save_positions(self) -> None:
        try:
            #  save positions
            positions = self.trading.get_account_positions(self.account)
            print(f'Saving Postions: {positions}')
            _d = dt.datetime.utcnow()
            dtime = dt.datetime(_d.year, _d.month, _d.day,
                                _d.hour, _d.minute, _d.second, 0, pytz.UTC)

            positions_event = Positions(ticker=f'real_positions_{conf.BROKER_FINANCIAL}',
                                        account=f'real_positions_{conf.BROKER_FINANCIAL}',
                                        positions=positions, datetime=dtime)
            self.emit.publish_event('positions', positions_event)

        except Exception as e:
            logger.error(f'Error Saving IB Positions: {e}')


    def send_broker(self, event) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        if event.event_type == 'order' and conf.SEND_ORDERS_BROKER_IB == 1:
            event.exchange_or_broker = self.exchange
            logger.info(f'Sending Order to broker {self.exchange} in ticker {event.ticker} quantity {event.quantity}')
            print(f'Sending Order to broker {self.exchange} in ticker {event.ticker} quantity {event.quantity}')
            self.trading.send_order(event, transmit=True)
        elif event.event_type == 'order' and conf.SEND_ORDERS_BROKER_IB == 0:
            event.exchange_or_broker = self.exchange
            print(f'Order for {event.ticker} recieved but not send.')


