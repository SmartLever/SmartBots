from smartbots.crypto.strategies.basic_strategy import Basic_Strategy, dataclass


class Simple_Avg_Cross(Basic_Strategy):
    """ Strategy Simple_Avg_Cross  using  Basic_Strategy as base class
        Have to be implemented add_event method with the logic of the strategy.

        Simple cross average strategy with two averages.

        Position could be 1 Long, 0 out of the market
        When short average cross long average, send order to buy if short average is above long average
        the position is 0.
        Parameters
        ----------
        params: dict
            Parameters of the strategy
            ticker: str - ticker of the asset
            short_period: int  Period of the short average
            long_period: int Period of the long average
            quantity: float  Quantity of the asset to buy or sell
    """

    def __init__(self, params, id_strategy=None, callback=None, set_basic=False):
        super().__init__(params, id_strategy, callback, set_basic)
        self.short_period = params['short_period']
        self.long_period = params['long_period']
        self.short_avg_value = None
        self.long_avg_value = None
        self.saves_values = {'datetime':[],'short_avg_value':[], 'long_avg_value':[], 'position':[], 'close':[]}

    def add_event(self,  event: dataclass):
        """ Logic of the Strategy"""
        if event.event_type == 'bar' and self.inicial_values:
            # Calculate short average
            self.short_avg_value = (self.short_avg_value * (self.short_period - 1) + event.close) / self.short_period
            # Calculate long average
            self.long_avg_value = (self.long_avg_value * (self.long_period - 1) + event.close) / self.long_period
            # Send order if cross average
            if self.short_avg_value > self.long_avg_value and self.position <= 0:
                self.send_order(ticker=event.ticker, price=event.close, quantity=self.parameters['quantity'],
                                action='buy', type='market',datetime=event.datetime)
                self.position = 1 # change position to Long
            elif self.short_avg_value < self.long_avg_value and self.position > 0:
                self.send_order(ticker=event.ticker, price=event.close, quantity=self.parameters['quantity'],
                                action='sell', type='market',datetime=event.datetime)
                self.position = 0 #change position out of the market
            # Save list of values
            self.saves_values['datetime'].append(event.datetime)
            self.saves_values['short_avg_value'].append(self.short_avg_value)
            self.saves_values['long_avg_value'].append(self.long_avg_value)
            self.saves_values['position'].append(self.position)
            self.saves_values['close'].append(event.close)

        elif event.event_type == 'bar' and self.inicial_values is False:
            # Calculate initial values
            self.short_avg_value = event.close
            self.long_avg_value = event.close
            self.inicial_values = True
