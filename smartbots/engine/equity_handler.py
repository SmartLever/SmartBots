"""  Calculate  and traking portfolio of stocks, futures, crypto from orders and prices"""

class Equity():
    def __init__(self, ticker: str, asset_type: str, fees: float = 0,
                 slippage: float = 0, point_value: float = 1, is_cost_percentage: bool = True):
        """Calcule equity for a ticker: could be stock, futures, crypto
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
        self.quantity = None
        self.datetime = None
        self.fees = fees
        self.slippage = slippage
        self.point_value = point_value
        self.is_cost_percentage = is_cost_percentage
        self.init = False

    def update(self, _update: dict):
        """Update equity with new price, quantity and datetime"""
        if self.init:
            cost = 0
            if _update['quantity'] != 0 and self.is_cost_percentage:# change in quantity, percentage of cost
                cost = abs(_update['price'] )* ( self.fees + self.slippage)
            elif _update['price'] != 0 and self.is_cost_percentage is False: # per 1 unit
                cost = abs(_update['quantity']) * (self.fees + self.slippage)
            self.equity +=  self.quantity * (_update['price'] - self.price) - cost
            self.datetime = _update['datetime']
            self.price = _update['price']
            if abs(_update['quantity'] ) > 0:
                self.quantity += _update['quantity']


        elif self.datetime is None:
            self.init = True
            self.datetime = _update['datetime']
            self.price = _update['price']
            self.quantity = _update['quantity']
            self.equity = 0


class Equity_Handler():
    def __init__(self,inicial_cash: float=100000, info_tickers: dict = {}):
        self.inicial_cash =inicial_cash
        self.current_holdings = {}
        self.equity = []
        self.equity_his = []
        self.ticker_to_equity = {}
        self.info_tickers = info_tickers
        self._populate_ticker_to_equity_from_info_tickers(info_tickers)

    def _populate_ticker_to_equity_from_info_tickers(self,info_tickers:dict):
        """
        This populates the ticker_to_equity dictionary with the information
        from the info_tickers dictionary.
        """
        for ticker in info_tickers.keys():
            if 'fees' not in info_tickers[ticker]:
                fees = 0
            else:
                fees = info_tickers[ticker]['fees']
            if 'slippage' not in  info_tickers[ticker]:
                slippage = 0
            else:
                slippage = info_tickers[ticker]['slippage']
            if 'point_value' not in info_tickers[ticker] and info_tickers[ticker]['asset_type'] in ['crypto', 'stocks']:
                point_value = 1
            else:
                point_value = info_tickers[ticker]['point_value']

            self.ticker_to_equity[ticker] = Equity(ticker, info_tickers[ticker]['asset_type'],
                                                   fees=fees,
                                                   slippage=slippage,
                                                   point_value=point_value)

    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all tickers.
        """
        pass

    def update(self, event):
        """ Update equity by event, it could be a bar event and order event or tick event"""
        if event.event_type == 'bar':
            update = {'quantity': 0, 'price': event.close,'datetime': event.datetime}
        elif event.event_type == 'order':
            quantity = event.quantity
            if event.action == 'sell':
                quantity = -quantity
            update = {'quantity': quantity, 'price': event.price, 'datetime': event.datetime}
        elif event.event_type == 'tick' and event.tick_type == 'close_day':
            update = {'quantity': 0, 'price': event.close, 'datetime': event.datetime}

        # check ir ticker is in ticker_to_equity
        if event.ticker in self.ticker_to_equity:
            # update equity
            self.ticker_to_equity[event.ticker].update(update)
        else:
            print(f'Ticker {event.ticker} not in ticker_to_equity')


if __name__ == '__main__':
    import pandas as pd
    import os
    from smartbots import conf
    # read sample data
    file = os.path.join(conf.path_to_crypto, 'data', 'example_for_equity.pkl')
    df = pd.read_pickle(file, compression='gzip')

    info_tickers = {'BTC-USDT': {'asset_type': 'crypto','point_value':1}}
    equity_handler = Equity_Handler(info_tickers=info_tickers)

    for event in df.events:
        equity_handler.update(event)