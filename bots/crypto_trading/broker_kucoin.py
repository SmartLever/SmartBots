""" Recieved events orders from Portfolio and send it to the broker or exchange for execution"""
import logging
logger = logging.getLogger(__name__)

def main(send_orders_status=True):
    from smartbots.decorators import log_start_end
    from smartbots.brokerMQ import receive_events
    import dataclasses
    from smartbots.crypto.kucoin_model import Trading


    def send_broker(_order: dict) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        order = _order['order']
        order.exchange = 'kucoin'
        trading.send_order(order)

    # Create trading object
    trading = Trading(send_orders_status=send_orders_status)
    receive_events(routing_key='order', callback=send_broker)

if __name__ == '__main__':
    main()