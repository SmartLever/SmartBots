from smartbots.abstractions.abstract_strategy import Abstract_Strategy, dataclass
from smartbots.indicators.simple_average import Simple_Average

class Simple_Avg_Cross(Abstract_Strategy):
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
        self.short_period = Simple_Average(self.parameters['short_period'])
        self.long_period = Simple_Average(self.parameters['long_period'])
        self.short_avg_value = None
        self.long_avg_value = None
        self.saves_values = {'datetime':[],'short_avg_value':[], 'long_avg_value':[], 'position':[], 'close':[]}
        self.type_trading = 'financial'

    def add_event(self,  event: dataclass):
        """ Logic of the Strategy goes here """
        if event.event_type == 'bar' and self.inicial_values: # logic with OHLC bars
            # Calculate short average
            self.short_avg_value = self.short_period.add(event.close)
            # Calculate long average
            self.long_avg_value = self.long_period.add(event.close)
            # Send order if cross average
            if self.short_avg_value > self.long_avg_value and self.position <= 0:
                self.send_order(ticker=event.ticker, price=event.close, quantity=self.parameters['quantity'],
                                action='buy', type='market',datetime=event.datetime)
            elif self.short_avg_value < self.long_avg_value and self.position > 0:
                self.send_order(ticker=event.ticker, price=event.close, quantity=self.parameters['quantity'],
                                action='sell', type='market',datetime=event.datetime)
            # Save list of values
            self.saves_values['datetime'].append(event.datetime)
            self.saves_values['short_avg_value'].append(self.short_avg_value)
            self.saves_values['long_avg_value'].append(self.long_avg_value)
            self.saves_values['position'].append(self.position)
            self.saves_values['close'].append(event.close)
            if self.bar_to_equity: # if bar_to_equity is True, save the equity by event bar.
                self.equity_hander_estrategy.update(event)

        elif event.event_type == 'bar' and self.inicial_values is False:
            # Calculate initial values
            self.short_avg_value = self.short_period.set_initial_value(event.close)
            self.long_avg_value = self.long_period.set_initial_value(event.close)
            self.inicial_values = True

        elif event.event_type == 'tick' and event.tick_type == 'close_day' and self.inicial_values:
            """Logic of the Strategy goes here for calculate data_crypto at the end of the day if it was necessary"""
            # update equity strategy
            self.update_equity(event)

