""" Recieved events bets from Portfolio and send it to the broker or exchange for execution"""
from src.application import conf
from src.domain.base_logger import logger
from typing import Dict
from src.infrastructure.betfair.betfair_model import Trading
from src.infrastructure.health_handler import Health_Handler
import datetime as dt


class BrokerBetfair(object):
    """
    Class
    for broker Betfair.

    """

    def __init__(self, config_brokermq: Dict = {}):
        self.config_brokermq = config_brokermq
        self.config_broker = {'USERNAME_BETFAIR': conf.USERNAME_BETFAIR, 'PASSWORD_BETFAIR': conf.PASSWORD_BETFAIR,
                              'APP_KEYS_BETFAIR': conf.APP_KEYS_BETFAIR}
        self.trading = Trading(config_broker= self.config_broker)
        self.health_handler = Health_Handler(n_check=6,
                                             name_service='broker_betfair',
                                             config=self.config_brokermq)

    def send_broker(self, bet: dict) -> None:
        """Send bet.

        Parameters
        ----------
        bet: event bet
        """
        if bet.event_type == 'bet':
            logger.info(f'Send Bet to broker in: {bet.match_name}')
            self.trading.send_order(bet)

    def check_balance(self) -> None:
        try:
            balance = self.trading.get_account_funds()['availableToBetBalance']
            print(f'Balance {balance} {dt.datetime.utcnow()}')
            self.health_handler.check()
        except Exception as e:
            logger.error(f'Error getting balance: {e}')
            self.health_handler.send(description=e, state=0)

