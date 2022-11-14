""" Data provider for Betfair.
    recieve data from Betfair websocket.
    Send Events to RabbitMQ for further processing.
"""
import os
from src.infrastructure.betfair.betfair_model import get_realtime_data
import datetime as dt
from src.infrastructure.brokerMQ import Emit_Events
from src.infrastructure.health_handler import Health_Handler
from src.domain.base_logger import logger
from src.application import conf


def main():

    def save_odds(odds) -> None:
        """ Populate Odds from data recieved from Betfair"""
        # Start publishing events in MQ
        emit.publish_event('odds', odds)
        health_handler.check()

    print(f'* Starting betfair provider at {dt.datetime.utcnow()}')
    config = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
              'password': conf.RABBITMQ_PASSWORD}
    health_handler = Health_Handler(n_check=1000,
                                    name_service=os.path.basename(__file__).split('.')[0],
                                    config=config)

    emit = Emit_Events(config=config)
    settings = {
        'time_books_play': 5,
        'time_books_not_play': 10,
        'time_events': 1800,
        'min_total_matched': 0,
        'minutes': 60,
        'event_ids': [1],
        # 'sports': ['soccer','tennis',basketball, horses],  # used by self.get_event_ids()
        'market_types': ['OVER_UNDER_25'],
        'betting_types': ['ODDS']}

    logger.info('Getting real data from Betfair')
    config_broker = {'USERNAME_BETFAIR': conf.USERNAME_BETFAIR, 'PASSWORD_BETFAIR': conf.PASSWORD_BETFAIR,
                     'APP_KEYS_BETFAIR': conf.APP_KEYS_BETFAIR}
    get_realtime_data(settings, callback=save_odds, config_broker=config_broker)


if __name__ == '__main__':
    main()