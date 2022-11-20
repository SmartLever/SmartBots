from src.application import conf
from src.infrastructure.brokerMQ import receive_events
import schedule
import time
import threading
if conf.BROKER_CRYPTO in ['kucoin', 'binance']:
    from src.application.bots.crypto_trading.ccxt.broker_ccxt import BrokerCCXT as BrokerCrypto


def main():

    def check_balance() -> None:
        broker.check_balance()

    def _schedule():
        # create scheduler for saving balance and positions
        schedule.every(60).seconds.do(check_balance)
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
    broker = BrokerCrypto(config_brokermq=config_brokermq, exchange_or_broker=conf.BROKER_CRYPTO)
    check_balance()
    # Launch thread to saving balance
    x = threading.Thread(target=_schedule)
    x.start()
    receive_events(routing_key='crypto_order', callback=send_broker, config=config_brokermq)


if __name__ == '__main__':
    main()