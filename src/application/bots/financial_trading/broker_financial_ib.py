from src.application import conf
from src.infrastructure.brokerMQ import receive_events
from src.application.bots.financial_trading.ib.broker_ib import BrokerIB as BrokerFinancial
import select

def main():

    def check_balance() -> None:
        broker.check_balance()

    def save_positions() -> None:
        broker.save_positions()

    def start_update_orders_status():
        broker.start_update_orders_status()

    def send_broker(order: dict) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        broker.send_broker(order)


    config_brokermq = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
                       'password': conf.RABBITMQ_PASSWORD}
    account = conf.ACCOUNT_IB
    # Create broker object
    broker = BrokerFinancial(config_brokermq=config_brokermq, exchange_or_broker=conf.BROKER_FINANCIAL, account=account)
    connection = receive_events(routing_key=conf.ROUTING_KEY, callback=send_broker, config=config_brokermq, block=False)
    sum = 0
    while True:
        try:
            # Wait until the socket has data available to read
            connection.process_data_events(time_limit=1)
        except select.error:
           print(select.error)
        sum += 1
        if sum == 10:
            # run balance
            check_balance()
            start_update_orders_status()
        elif sum == 90:
            sum = 0
            # run save_positions
            save_positions()


if __name__ == '__main__':
    main()