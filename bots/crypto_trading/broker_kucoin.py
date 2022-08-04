""" Recieved events orders from Portfolio and send it to the broker or exchange for execution"""
import logging
logger = logging.getLogger(__name__)

def main():
    from smartbots.decorators import log_start_end
    from smartbots.brokerMQ import Emit_Events,receive_events
    import dataclasses
    from smartbots.crypto.kucoin_model import Trading


    def send_broker(order: dataclasses.dataclass) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        trading.send_order(order)

    # Create trading object
    trading = Trading()
    # Connect to brokerMQ for receiving orders
    receive_events(routing_key='order', callback=send_broker)

if __name__ == '__main__':
    main()