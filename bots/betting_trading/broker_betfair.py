""" Recieved events bets from Portfolio and send it to the broker or exchange for execution"""
import logging
logger = logging.getLogger(__name__)


def main():
    from smartbots.brokerMQ import receive_events
    from smartbots.betting.betfair_model import Trading

    def send_broker(_bet: dict) -> None:
        """Send bet.

        Parameters
        ----------
        bet: event bet
        """
        if _bet.event_type == 'bet':
            trading.send_order(_bet)

    # Create trading object
    trading = Trading()
    receive_events(routing_key='bet', callback=send_broker)


if __name__ == '__main__':
    main()