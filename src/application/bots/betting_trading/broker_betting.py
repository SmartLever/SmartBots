from src.application import conf
from src.infrastructure.brokerMQ import receive_events
import schedule
import time
import threading
if conf.BROKER_BETTING == 'betfair':
    from src.application.bots.betting_trading.betfair.broker_betfair import BrokerBetfair as BrokerBetting


def main():

    def check_balance() -> None:
        broker.check_balance()

    def schedule_balance():
        # create scheduler for saving balance
        schedule.every(1).minutes.do(check_balance)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def send_broker(bet: dict) -> None:
        """Send bet.

        Parameters
        ----------
        bet: event bet
        """
        broker.send_broker(bet)

    # Log event health of the service
    config_brokermq = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
                       'password': conf.RABBITMQ_PASSWORD}
    # Create broker object
    broker = BrokerBetting(config_brokermq=config_brokermq)
    check_balance()
    # Launch thread to saving balance
    x = threading.Thread(target=schedule_balance)
    x.start()
    receive_events(routing_key='bet', callback=send_broker, config=config_brokermq)


if __name__ == '__main__':
    main()