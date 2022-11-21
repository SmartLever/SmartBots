from src.application import conf
from src.infrastructure.brokerMQ import receive_events
import schedule
import time
import threading
if conf.BROKER_FINANCIAL == 'darwinex':
    from src.application.bots.financial_trading.mt4.broker_mt4 import BrokerMT4 as BrokerFinancial


def main():

    def check_balance() -> None:
        broker.check_balance()

    def save_positions() -> None:
        broker.save_positions()

    def _schedule():
        # create scheduler for saving balance and positions
        schedule.every(15).seconds.do(check_balance)
        schedule.every(15).seconds.do(save_positions)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def send_broker(order: dict) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        broker.send_broker(order)

    config_brokermq = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
                       'password': conf.RABBITMQ_PASSWORD}
    # Create broker object
    broker = BrokerFinancial(config_brokermq=config_brokermq, exchange_or_broker=conf.BROKER_FINANCIAL)
    check_balance()
    # Launch thread to saving balance
    x = threading.Thread(target=_schedule)
    x.start()
    receive_events(routing_key=conf.ROUTING_KEY, callback=send_broker, config=config_brokermq)


if __name__ == '__main__':
    main()