from src.application import conf
if conf.BROKER_BETTING == 'betfair':
    from src.application.bots.betting_trading.betfair.data_betfair import ProviderBetfair as ProviderBetting


def main():

    def get_realtime_data() -> None:
        provider.get_realtime_data()

    # Log event health of the service
    config_brokermq = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
                       'password': conf.RABBITMQ_PASSWORD}
    # Create broker object
    provider = ProviderBetting(config_brokermq=config_brokermq)
    get_realtime_data()


if __name__ == '__main__':
    main()