""" Recieved events orders from Portfolio and send it to the broker or exchange for execution"""
import logging

logger = logging.getLogger(__name__)


def main(send_orders_status=True, exchange='kucoin'):
    from smartbots.decorators import log_start_end
    from smartbots.brokerMQ import receive_events
    import datetime as dt
    from smartbots.crypto.exchange_model import Trading
    import schedule
    from smartbots import conf
    from smartbots.health_handler import Health_Handler
    import time
    import threading

    def check_balance() -> None:
        try:
            balance = trading.get_total_balance('USD')
            print(f'Balance {balance} {dt.datetime.utcnow()}')
            health_handler.check()
        except Exception as e:
            health_handler.send(description=e, state=0)

    def schedule_balance():
        # create scheduler for saving balance
        schedule.every(10).minutes.do(check_balance)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def send_broker(event) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        if event.event_type == 'order' and conf.SEND_ORDERS_BROKER == 1:
            event.exchange = exchange
            trading.send_order(event)
        elif event.event_type == 'order' and conf.SEND_ORDERS_BROKER == 0:
            event.exchange = exchange
            print(f'Order for {event.ticker} recieved but not send.')

    # Log event health of the service
    health_handler = Health_Handler(n_check=6,
                                    name_service=f'broker_{exchange}')
    # Create trading object
    trading = Trading(send_orders_status=send_orders_status, exchange=exchange)
    check_balance()
    # Launch thread to saving balance
    x = threading.Thread(target=schedule_balance)
    x.start()
    # Launch thead for update orders status
    trading.start_update_orders_status()

    receive_events(routing_key='order', callback=send_broker)


if __name__ == '__main__':
    exchange = 'kucoin'
    main(exchange =exchange)
