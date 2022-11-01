"""  Calculate  and traking portfolio of stocks, futures, crypto from orders and prices"""
import pandas as pd
import datetime as dt
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
        self.equity_pct = None # porcentage equity
        self.equity_vector = [] # equity vector
        self.equity_day = []  # equity vector
        self.quantity = None
        self.datetime = None
        self.leverage = 0
        self.fees = fees
        self.slippage = slippage
        self.point_value = point_value
        self.is_cost_percentage = is_cost_percentage
        self.init = False
        self.id_strategy = id_strategy

    def fill_equity_vector(self):
        self.equity_vector.append({'datetime': self.datetime, 'equity': self.equity,'equity_pct': self.equity_pct,
                                   'quantity': self.quantity,'price': self.price,'leverage': self.leverage})

    def fill_equity_day(self):
        dtime = dt.datetime(self.datetime.year, self.datetime.month, self.datetime.day)
        self.equity_day.append({'datetime': dtime, 'equity': self.equity,'equity_pct': self.equity_pct,
                                   'quantity': self.quantity,'price': self.price, 'leverage': self.leverage})

    def get_equity_vector(self):
        df = pd.DataFrame(self.equity_vector)
        df.set_index('datetime', inplace=True)
        df['ticker'] = self.ticker
        df['diff'] = df['equity'].diff().fillna(0)
        df['id_strategy'] = self.id_strategy
        return df

    def get_equity_day(self):
        df = pd.DataFrame(self.equity_day)
        df.set_index('datetime', inplace=True)
        df['ticker'] = self.ticker
        df['diff'] = df['equity'].diff().fillna(0)
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
            var = self.quantity * (_update['price'] - self.price) * self.point_value - cost
            self.equity += var
            self.leverage = abs(self.quantity * self.price) / self.price
            # equity porcentage
            self.equity_pct = self.equity_pct * (var/(self.price*self.point_value)) +self.equity_pct
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
            self.leverage = 0
            self.equity_pct = 100


class Equity_Handler():
    def __init__(self,inicial_cash: float= 0,ticker_to_strategies: dict = None):
        """Calculate equity for a portfolio of tickers
                Parameters
                ----------
                inicial_cash: inicial cash for the portfolio
                ticker_to_strategies: strategies object for the portfolio
        """

        self.inicial_cash =inicial_cash
        self.current_holdings = {}
        self.ticker_to_strategies = ticker_to_strategies # pointer to strategies
        self.equity_day = []



    def get_equities(self):
        """
        This returns the equity of components of the portfolio.
        """
        df = []
        df_day = []
        for ticker in self.ticker_to_strategies.keys():
            for strategy in self.ticker_to_strategies[ticker]:
                frame = strategy.equity_hander_estrategy.get_equity_vector()
                df.append(frame)
                frame_day = strategy.equity_hander_estrategy.get_equity_day()
                df_day.append(frame_day)
        port = pd.DataFrame(self.equity_day)
        port.set_index('datetime', inplace=True)
        return {'equities_by_events': df, 'equities_by_day':df_day,
                'equity_portfolio': port}

    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all tickers.
        """
        pass

    def calculate_equity_day(self, _datetime: dt.datetime):
        """
        Calculate equity of the portfolio for last day.
        """
        dtime = dt.datetime(_datetime.year, _datetime.month, _datetime.day) # by date
        equity = {'datetime': dtime, 'equity': self.inicial_cash}
        # Get equity for strategy and sum with total
        for ticker in self.ticker_to_strategies.keys():
            for strategy in self.ticker_to_strategies[ticker]:
                value = strategy.equity_hander_estrategy.equity
                if value is None:
                    value = 0
                equity['equity'] += value
        # update equity day
        if len(self.equity_day) > 0:
            if equity['datetime'] == self.equity_day[-1]['datetime']:
                self.equity_day[-1] = equity
            elif equity['datetime'] > self.equity_day[-1]['datetime']:
                self.equity_day.append(equity)
        else:
            self.equity_day.append(equity)

