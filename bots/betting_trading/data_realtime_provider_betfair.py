""" Data provider for Betfair.
    recieve data from Betfair websocket.
    Send Events to RabbitMQ for further processing.
"""
import logging
from smartbots.betting.betfair_model import  get_realtime_data
import datetime as dt
import pandas as pd
from smartbots.events import Odds
import schedule
import time
import threading
from smartbots.decorators import log_start_end
from smartbots.brokerMQ import Emit_Events

logger = logging.getLogger(__name__)


async def save_odds(msg=dict) -> None:
    """ Populate Odds from data recieved from Betfair"""
    odds = Odds()
    # Start publishing events in MQ
    emit = Emit_Events('odds',odds)
    print(odds)


if __name__ == '__main__':
    print(f'* Starting betfair provider at {dt.datetime.utcnow()}')
    global save_data
    tickers = []  # events
    get_realtime_data(tickers, save_odds)
