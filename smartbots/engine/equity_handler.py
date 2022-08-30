"""  Calculate  and traking portfolio of stocks, futures, crypto from orders and prices"""



class Equity():
    def __init__(self, ticker: str, asset_type: str, fees: float = 0,
                 slippage: float = 0, point_value: float = 1):
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
        self.init = False

    def update(self, _update: dict):
        """Update equity with new price, quantity and datetime"""
        if self.init:
            cost = 0
            if _update['quantity'] != 0:# change in quantity, add cost
                cost = (_update['price'] * _update['quantity']) * (1 + self.fees) * (1 + self.slippage)
            self.equity = self.equity + self.quantity * (_update['price'] - self.price) - cost
            self.quantity += _update['quantity']
            self.datetime = _update['datetime']
            self.price = _update['price']

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
            if 'fees' in info_tickers[ticker]:
                fees = 0
            else:
                fees = self.fees
            if 'slippage' in info_tickers[ticker]:
                slippage = 0
            else:
                slippage = self.slippage
            if 'point_value' not in  info_tickers[ticker] and info_tickers[ticker]['asset_type'] in ['crypto', 'stocks']:
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
        """ Update equity by event, it could be a bar event and order event or close_day event"""
        if event.event_type == 'bar':
            update = {'quantity': 0, 'price': event.close,'datetime': event.datetime}
        elif event.event_type == 'order':
            quantity = event.quantity
            if event.action == 'sell':
                quantity = -quantity
            update = {'quantity': quantity, 'price': event.price,'datetime': event.datetime}
        elif event.event_type == 'close_day':
            update = {'quantity': 0, 'price': event.close,'datetime': event.datetime}

        # check ir ticker is in ticker_to_equity
        if event.ticker in self.ticker_to_equity:
            # update equity
            self.ticker_to_equity[event.ticker].update(update)
        else:
            print(f'Ticker {event.ticker} not in ticker_to_equity')