import datetime as dt
from src.application import conf
from src.application.base_logger import logger
import schedule
import time
import threading
if conf.BROKER_FINANCIAL == 'ftmo':
    from src.application.bots.financial_trading.mt4.data_mt4 import ProviderMT4 as ProviderFinancial


def main():

    def get_stream_quotes_changes() -> None:
        provider.get_stream_quotes_changes()

    def create_bar():
        provider.create_bar()

    def create_tick_closed_day():
        provider.create_tick_closed_day()

    def create_timer():
        provider.create_timer()

    def schedule_broker():
        # create scheduler for bar event
        schedule.every().minute.at(":00").do(create_bar)
        # create scheduler for close_day event
        schedule.every().day.at("00:00").do(create_tick_closed_day)
        schedule.every().minute.at(":00").do(create_timer)
        while True:
            schedule.run_pending()
            time.sleep(1)

    print(f'* Starting MT4 provider at {dt.datetime.utcnow()}')
    logger.info(f'Starting MT4 provider at {dt.datetime.utcnow()}')
    symbols = conf.FINANCIAL_SYMBOLS
    # Log event health of the service
    config_brokermq = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
                       'password': conf.RABBITMQ_PASSWORD}
    # Create broker object
    provider = ProviderFinancial(config_brokermq=config_brokermq, symbols=symbols,
                                 exchange_or_broker=conf.BROKER_FINANCIAL)
    x = threading.Thread(target=schedule_broker)
    x.start()
    #  Get real data
    get_stream_quotes_changes()


if __name__ == '__main__':
    main()