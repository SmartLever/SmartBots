"""  Calculate  and traking portfolio of stocks, futures, crypto from orders and prices"""
import pandas as pd
class Equity():
    def __init__(self, ticker: str, asset_type: str, fees: float = 0,
                 slippage: float = 0, point_value: float = 1, is_cost_percentage: bool = True, id_strategy=-1):
        """Calcule equity for a ticker: could be stock, futures, crypto
                Parameters
                ----------
                ticker: ticker for calculating the equity, has to be a unique asset
                asset_type: crypto, futures, stocks, currency
                fees: fees of buying or selling one unit, percentage
                slippage: slippage between real price and simulated, percentage
                id_strategy: id_strategy for the equity, if not set, it will be -1
        """
        self.ticker = ticker
        self.asset_type = asset_type
        self.price = None
        self.equity = None
        self.equity_vector = [] # equity vector
        self.quantity = None
        self.datetime = None
        self.fees = fees
        self.slippage = slippage
        self.point_value = point_value
        self.is_cost_percentage = is_cost_percentage
        self.init = False
        self.id_strategy = id_strategy

    def fill_equity_vector(self):
        self.equity_vector.append({'datetime': self.datetime, 'equity': self.equity,
                                   'quantity': self.quantity,'price': self.price})

    def get_equity_vector(self):
        df = pd.DataFrame(self.equity_vector)
        df.set_index('datetime', inplace=True)
        df['ticker'] = self.ticker
        df['id_strategy'] = self.id_strategy
        return df

    def update(self, _update: dict):
        """Update equity with new price, quantity and datetime"""
        if self.init:
            cost = 0
            if _update['quantity'] != 0 and self.is_cost_percentage:# change in quantity, percentage of cost
                cost = abs(_update['price']) * (self.fees + self.slippage)
            elif _update['price'] != 0 and self.is_cost_percentage is False: # per 1 unit
                cost = abs(_update['quantity']) * (self.fees + self.slippage)
            self.equity += self.quantity * (_update['price'] - self.price) - cost
            self.datetime = _update['datetime']
            self.price = _update['price']
            if abs(_update['quantity']) > 0:
                self.quantity += _update['quantity']
        elif self.datetime is None:
            self.init = True
            self.datetime = _update['datetime']
            self.price = _update['price']
            self.quantity = _update['quantity']
            self.equity = 0


class Equity_Handler():
    def __init__(self,inicial_cash: float=100000, info_tickers: dict = {},ticker_to_id_strategies: dict = {},
                 save_equity_vector_for: list = ['close_day','order']):
        """Calculate equity for a portfolio of tickers
                Parameters
                ----------
                inicial_cash: inicial cash for the portfolio
                info_tickers: dictionary with info of tickers
                ticker_to_id_strategies: dictionary with id of strategies for each ticker
                save_equity_vector_for: list of events to save equity vector
        """
        if len(info_tickers) == 0:
            raise ValueError('info_tickers is empty')
        self.inicial_cash =inicial_cash
        self.save_equity_vector_for = save_equity_vector_for
        self.ticker_to_id_strategies = ticker_to_id_strategies
        self.current_holdings = {}
        self.ticker_to_equity = {} # equity by ticker
        self.ticker_to_id_to_equity = {} # equity by strategy and ticker
        self.info_tickers = info_tickers
        self._init_equities() # initialize equity for each ticker and strategy

    def _init_equities(self):
        """
        This initializes the equity for each ticker and id.
        """
        if len(self.ticker_to_id_to_equity) > 0:
            for ticker in self.ticker_to_id_strategies.keys():
                self.ticker_to_equity[ticker] = self._create_equity(ticker)
                self.ticker_to_id_to_equity[ticker] = {}
                for id_strategy in self.ticker_to_id_strategies[ticker]:
                    self.ticker_to_id_to_equity[ticker][id_strategy] = self._create_equity(ticker)
        else: # only one equity for each ticker, no strategies
            for ticker_info in self.info_tickers:
                self.ticker_to_equity[ticker_info['ticker']] = self._create_equity(ticker_info['ticker'])
                self.ticker_to_id_to_equity[ticker_info['ticker']] = {}


    def get_equities(self):
        """
        This returns the equity of components of the portfolio.
        """
        df = []
        for ticker_equity in self.ticker_to_equity.values():
            df.append(ticker_equity.get_equity_vector())
            for id_strategy_equity in self.ticker_to_id_to_equity[ticker_equity.ticker].values():
                df.append(id_strategy_equity.get_equity_vector())
        return df

    def _create_equity(self, ticker: str, id_strategy: int = -1):
        """
        create equity for a ticker
        """
        # extract from info_tickers the info for ticker
        for ticker_info in self.info_tickers:
            if ticker_info['ticker'] == ticker:
                if 'fees' not in ticker_info:
                    fees = 0
                else:
                    fees = ticker_info['fees']
                if 'slippage' not in ticker_info:
                    slippage = 0
                else:
                    slippage = ticker_info['slippage']
                if 'point_value' not in ticker_info and ticker_info['asset_type'] in ['crypto', 'stocks']:
                    point_value = 1
                else:
                    point_value = ticker_info['point_value']

                return Equity(ticker, ticker_info['asset_type'],fees=fees,
                              slippage=slippage,point_value=point_value,id_strategy=id_strategy)

    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all tickers.
        """
        pass

    def update(self, event):
        """ Update equity by event, it could be a bar event and order event or tick event"""
        save_vector = False
        if event.event_type in self.save_equity_vector_for:
            save_vector = True
        if event.event_type == 'bar':
            update = {'quantity': 0, 'price': event.close, 'datetime': event.datetime}
        elif event.event_type == 'order':
            quantity = event.quantity
            if event.action == 'sell':
                quantity = -quantity
            update = {'quantity': quantity, 'price': event.price, 'datetime': event.datetime}
        elif event.event_type == 'tick' and event.tick_type == 'close_day':
            update = {'quantity': 0, 'price': event.price, 'datetime': event.datetime}
            if 'close_day' in self.save_equity_vector_for:
                save_vector = True
        # check if ticker is in ticker_to_equity
        if event.ticker in self.ticker_to_equity:
            # update equity for ticker
            self.ticker_to_equity[event.ticker].update(update)
            if save_vector: # save values
                self.ticker_to_equity[event.ticker].fill_equity_vector()
            # update equity for id_strategy
            for id_strategy_equity in self.ticker_to_id_to_equity[event.ticker].values():
                id_strategy_equity.update(update)
                if save_vector:
                    id_strategy_equity.fill_equity_vector()
        else:
            print(f'Ticker {event.ticker} not in ticker_to_equity')


if __name__ == '__main__':
    import pandas as pd
    import os
    from smartbots import conf
    # read sample data
    file = os.path.join(conf.path_to_crypto, 'data', 'example_for_equity.pkl')
    df = pd.read_pickle(file, compression='gzip')
    df = df.sort_index()

    info_tickers = [{'ticker':'BTC-USDT','asset_type': 'crypto', 'point_value':1},
                    {'ticker':'ETH-USDT','asset_type': 'crypto', 'point_value':1}]
    equity_handler = Equity_Handler(info_tickers=info_tickers)

    for event in df.events:
        equity_handler.update(event)

    stop = 1