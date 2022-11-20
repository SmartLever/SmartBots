""" Portfolio Production Bot.
    This bot is used to produce a portfolio of crypto currencies or financial securities.
    It is used to:
    1) Test the perfomance of a combination of strategies.
    2) Test the stats of a strategy with a portfolio.
    3) Run in real time.

    Here the configuration is done in the config_crypto.yaml file.
    The configuration is done in the following way:
    1) The configuration is read from the config_crypto.yaml file.
    2) The configuration is validated.
    3) The configuration is used to create the portfolio.
    4) The configuration is used to connect to the data source, run the simulation and run in real time
    to produce orders that will send to trading.
    """
import datetime as dt


def main(run_real: bool = False, send_orders_to_broker: bool = True,
         start_date: dt.datetime = dt.datetime(2022, 7, 1),conf_portfolio: str=None ,
         asset_type: str=None) -> None:
    """ Run the portfolio engine. """
    from src.domain.config_helper import get_config
    import os
    import pandas as pd
    from src.application import conf
    from src.application.services.portfolio_constructor import Portfolio_Constructor
    path = os.path.abspath(__file__)
    path_bot = os.path.dirname(path)  # path to the module
    path_to_config = os.path.join(conf.path_to_data, "config_portfolios", conf_portfolio+".yaml")
    conf_portfolio = get_config(path_to_config)  # get the configuration from the config file
    # if our strategy is in a csv file
    list_strategy = []
    if conf_portfolio['Strategies_Load_From']['from']:
        # load strategy from csv
        path_info_strategy = os.path.join(path_bot, f'{asset_type}_trading', conf_portfolio['Strategies_Load_From']['from'])
        info_strategy = pd.read_csv(path_info_strategy)
        for index, strategy in info_strategy.iterrows():
            dict_strategy = {'params': {}}
            for k in strategy.keys():
                if k == 'id':
                    dict_strategy['id'] = strategy[k]
                elif k == 'name':
                    dict_strategy['strategy'] = strategy[k]
                else:
                    dict_strategy['params'][k] = strategy[k]
            list_strategy.append(dict_strategy)
        conf_portfolio['Strategies'] = list_strategy

    # run the portfolio engine, set run_real=True to run in real time
    portfolio_production = Portfolio_Constructor(conf_portfolio, run_real=run_real, asset_type=asset_type,
                                                 send_orders_to_broker=send_orders_to_broker, start_date=start_date)
    portfolio_production.run()


if __name__ == '__main__':
    run_real = True
    asset_type = 'financial'
    conf_portfolio = 'config_financial'
    start_date = dt.datetime(2018, 1, 1)
    main(run_real=run_real, send_orders_to_broker=True, start_date=start_date,
         conf_portfolio=conf_portfolio,asset_type=asset_type)
