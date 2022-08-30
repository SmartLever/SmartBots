""" Compute equity from orders"""


class Equity():
    def __init__(self, ticker: str, asset_type: str, fees: float = 0,
                 slippage: float = 0, point_value: float = 1):
        """Calcule equity for a ticker
                Parameters
                ----------
                ticker: ticker for calculating the equity, has to be a unique asset
                asset_type: crypto, futures, stocks, currency
                fees: fees of buying or selling one unit, percentage
                slippage: slippage between real price and simulated, percentage

        """
        self.ticker = ticker
        self.asset_type = asset_type
        self.price = None
        self.equity = None
        self.fees = fees
        self.slippage = slippage
        self.point_value = point_value

    def add(self):
        pass

class Equity_Handler():
    def __init__(self,inicial_cash: float=100000):
        self.inicial_cash =inicial_cash
        self.current_holdings = {}
        self.equity = []
        self.equity_his = []
        self.ticker_to_equity = {}

    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all tickers.
        """
        pass

    def update(self,event):
        """ Update equity by event, it could be a bar event and order event or close_day event"""
        event
