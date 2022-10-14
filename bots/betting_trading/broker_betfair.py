""" Recieved events bets from Portfolio and send it to the broker or exchange for execution"""
from smartbots.base_logger import logger

def main():
    from smartbots.brokerMQ import receive_events
    from smartbots.betting.betfair_model import Trading
    from smartbots.health_handler import Health_Handler
    import datetime as dt
    import schedule
    import time
    import threading

    def check_balance() -> None:
        try:
            balance = trading.get_account_funds()['availableToBetBalance']
            print(f'Balance {balance} {dt.datetime.utcnow()}')
            health_handler.check()
        except Exception as e:
            logger.error(f'Error getting balance: {e}')
            health_handler.send(description=e, state=0)

    def schedule_balance():
        # create scheduler for saving balance
        schedule.every(1).minutes.do(check_balance)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def send_broker(_bet: dict) -> None:
        """Send bet.

        Parameters
        ----------
        bet: event bet
        """
        if _bet.event_type == 'bet':
            logger.info(f'Send Bet to broker in: {_bet.match_name}')
            trading.send_order(_bet)

    # Log event health of the service
    health_handler = Health_Handler(n_check=6,
                                    name_service='broker_betfair')

    # Create trading object
    trading = Trading()
    check_balance()
    # Launch thread to saving balance
    x = threading.Thread(target=schedule_balance)
    x.start()
    receive_events(routing_key='bet', callback=send_broker)


if __name__ == '__main__':
    main()