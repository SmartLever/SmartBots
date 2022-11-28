import datetime as dt
from src.application import conf
from src.application.base_logger import logger
import schedule
import time
import threading
if conf.BROKER_CRYPTO in ['kucoin', 'binance']:
    from src.application.bots.crypto_trading.ccxt.provider_ccxt import ProviderCCXT as ProviderCrypto


def main():

    def create_bar():
        provider.create_bar()

    def create_tick_closed_day():
        provider.create_tick_closed_day()

    def schedule_broker():
        # create scheduler for bar event
        schedule.every().minute.at(":00").do(create_bar)
        # create scheduler for close_day event
        schedule.every().day.at("00:00").do(create_tick_closed_day)
        while True:
            schedule.run_pending()
            time.sleep(1)

    print(f'* Starting crypto provider at {dt.datetime.utcnow()}')
    logger.info(f'Starting crypto provider r at {dt.datetime.utcnow()}')
    symbols = ['BTC-USDT', 'ETH-USDT']
    # Log event health of the service
    config_brokermq = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
                       'password': conf.RABBITMQ_PASSWORD}
    # Create broker object
    provider = ProviderCrypto(config_brokermq=config_brokermq, symbols=symbols,
                              exchange_or_broker=conf.BROKER_CRYPTO)
    x = threading.Thread(target=schedule_broker)
    x.start()


if __name__ == '__main__':
    main()