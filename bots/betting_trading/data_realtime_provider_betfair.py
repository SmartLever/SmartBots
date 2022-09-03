""" Data provider for Betfair.
    recieve data from Betfair websocket.
    Send Events to RabbitMQ for further processing.
"""
import logging
from smartbots.betting.betfair_model import get_realtime_data
import datetime as dt
from smartbots.brokerMQ import Emit_Events

logger = logging.getLogger(__name__)


def main():

    def save_odds(odds) -> None:
        """ Populate Odds from data recieved from Betfair"""
        # Start publishing events in MQ
        emit.publish_event('odds', odds)
        print(odds)

    print(f'* Starting betfair provider at {dt.datetime.utcnow()}')
    emit = Emit_Events()
    settings = {
        'time_books_play': 5,
        'time_books_not_play': 10,
        'time_events': 1800,
        'min_total_matched': 0,
        'minutes': 60,
        'event_ids': [1],
        # 'sports': ['soccer','tennis',basketball, horses],  # used by self.get_event_ids()
        'market_types': ['OVER_UNDER_25', 'OVER_UNDER_05'],
        'betting_types': ['ODDS']}
    get_realtime_data(settings, callback=save_odds)


if __name__ == '__main__':
    main()