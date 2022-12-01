""" Recieved events orders from Portfolio and send it to the broker or exchange for execution"""
from src.application.base_logger import logger
from typing import Dict
from src.application import conf
import datetime as dt
from src.infrastructure.crypto.exchange_handler import Trading
from src.application.services.health_handler import Health_Handler

class BrokerCCXT(object):
    """
    Class
    for broker ccxt.

    """
    def __init__(self, config_brokermq: Dict = {}, send_orders_status=True, exchange_or_broker='kucoin'):
        self.config_brokermq = config_brokermq
        self.exchange = exchange_or_broker
        self.trading = Trading(send_orders_status=send_orders_status, exchange_or_broker=exchange_or_broker,
                               config_brokermq=config_brokermq)
        # Log event health of the service
        self.health_handler = Health_Handler(n_check=6,
                                             name_service=f'broker_{exchange_or_broker}',
                                             config=config_brokermq)
        # Launch thead for update orders status
        self.trading.start_update_orders_status()

    def check_balance(self) -> None:
        try:
            balance = self.trading.get_total_balance()
            logger.info(f'Balance {balance} {dt.datetime.utcnow()} in broker {self.exchange}')
            print(f'Balance {balance} {dt.datetime.utcnow()}')
            self.health_handler.check()
        except Exception as e:
            logger.error(f'Error Getting {self.exchange} Balance: {e}')
            self.health_handler.send(description=e, state=0)

    def send_broker(self, event) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        if event.event_type == 'order' and conf.SEND_ORDERS_BROKER == 1:
            event.exchange_or_broker = self.exchange
            logger.info(f'Sending Order to broker {self.exchange} in ticker {event.ticker} quantity {event.quantity}')
            self.trading.send_order(event)
        elif event.event_type == 'order' and conf.SEND_ORDERS_BROKER == 0:
            event.exchange_or_broker = self.exchange
            print(f'Order for {event.ticker} recieved but not send.')
