from abc import ABC
import dataclasses
from datetime import datetime
from typing import Dict, List


async def _callable(data: Dict) -> None:
    """Callback function for realtime data. [Source: MT4]

    Parameters
    ----------
    data: Dict
        Realtime data.
    """
    print(data)

class Abstract_Trading(ABC):
    """ Abstract class for Betting Broker
    All brokers must inherit from this class"""
    def __init__(self, settings_real_time: dict = {}, callback_real_time: callable = _callable,
                 exchange_or_broker: str = 'betfair', config_broker: Dict = {}):

        self.exchange_or_broker = exchange_or_broker
        self.config_broker = config_broker
        self.client = self.get_client()
        self.settings_real_time = settings_real_time
        self.next_events = {}  # dict to saving markets
        self.last_datetime = {}  # dict to saving last datetime from ticker
        self.callback_real_time = callback_real_time

    def get_client(self):
        # to be implemented in the child class
        pass

    def send_order(self, bet: dataclasses.dataclass) -> None:
        """Send order.

        Parameters
        ----------
        bet: event bet
        """
        # to be implemented in the child class
        pass

    def get_current_bets(self) -> List:
        """
        get current bets
        :return:
            list of currents bets
        """
        # to be implemented in the child class
        pass

    def get_settled_bets(self, init_datetime=datetime(2022, 8, 1), end_datetime=datetime.now(), req_id=1) -> List:
        """
        get settled bets
        :param init_datetime:
        :param end_datetime:
        :param req_id: by default is 1
        :return:
            list of settled bets between 2 two dates
        """
        # to be implemented in the child class
        pass

    def cancel_bet(self, bet: dataclasses.dataclass) -> None:
        """ Cancel bet
        Parameters
        ----------
        bet: event bet
        """
        # to be implemented in the child class
        pass

    def get_account_details(self) -> Dict:
        """ get details from account"""
        # to be implemented in the child class
        pass

    def get_account_funds(self) -> Dict:
        """ get balance from account"""
        # to be implemented in the child class
        pass