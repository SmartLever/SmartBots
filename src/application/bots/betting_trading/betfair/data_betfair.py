""" Data provider for Betfair.
    recieve data from Betfair websocket.
    Send Events to RabbitMQ for further processing.
"""
from src.application import conf
from src.domain.base_logger import logger
from typing import Dict
from src.infrastructure.betfair.betfair_model import Trading
from src.infrastructure.health_handler import Health_Handler
from src.infrastructure.brokerMQ import Emit_Events
from src.infrastructure.betfair.betfair_model import get_realtime_data


class ProviderBetfair(object):
    """
    Class
    for provider Betfair.

    """

    def __init__(self, config_brokermq: Dict = {}):
        self.config_brokermq = config_brokermq
        self.config_broker = {'USERNAME_BETFAIR': conf.USERNAME_BETFAIR, 'PASSWORD_BETFAIR': conf.PASSWORD_BETFAIR,
                              'APP_KEYS_BETFAIR': conf.APP_KEYS_BETFAIR}
        self.trading = Trading(config_broker= self.config_broker)
        self.health_handler = Health_Handler(n_check=6,
                                             name_service='data_realtime_provider_betfair',
                                             config=self.config_brokermq)
        self.emit = Emit_Events(config=config_brokermq)
        self.settings = {
            'time_books_play': 5,
            'time_books_not_play': 10,
            'time_events': 1800,
            'min_total_matched': 0,
            'minutes': 60,
            'event_ids': [1],
            # 'sports': ['soccer','tennis',basketball, horses],  # used by self.get_event_ids()
            'market_types': ['OVER_UNDER_25'],
            'betting_types': ['ODDS']}

    def save_odds(self, odds) -> None:
        """ Populate Odds from data recieved from Betfair"""
        # Start publishing events in MQ
        self.emit.publish_event('odds', odds)
        self.health_handler.check()

    def get_realtime_data(self) -> None:
        logger.info('Getting real data from Betfair')
        get_realtime_data(self.settings, callback=self.save_odds, config_broker=self.config_broker)