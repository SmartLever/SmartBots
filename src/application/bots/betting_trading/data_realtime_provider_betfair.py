""" Data provider for Betfair.
    recieve data from Betfair websocket.
    Send Events to RabbitMQ for further processing.
"""
import os
from src.infraestructure.api_berfair.betfair_model import get_realtime_data
import datetime as dt
from src.infraestructure.brokerMQ import Emit_Events
from src.infraestructure.health_handler import Health_Handler
from src.domain.base_logger import logger


def main():

    def save_odds(odds) -> None:
        """ Populate Odds from data recieved from Betfair"""
        # Start publishing events in MQ
        emit.publish_event('odds', odds)
        health_handler.check()

    print(f'* Starting betfair provider at {dt.datetime.utcnow()}')
    health_handler = Health_Handler(n_check=1000,
                                    name_service=os.path.basename(__file__).split('.')[0])

    emit = Emit_Events()
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
    get_realtime_data(settings, callback=save_odds)


if __name__ == '__main__':
    main()