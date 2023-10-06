from src.domain.abstractions.abstract_strategy import Abstract_Strategy, Order
from dataclasses import dataclass
import datetime as dt

# errores: podria haber puesto un valor por defecto a los parametros parq que sea mas intuitivo, cuando enviar la orden deberia cambiar el valor de
# self.position para que no envie multiples ordenes, y cuando el evento es tick o close_day , deberia haber actualizado la equity
# le ha faltado poner el argumento set_basic, tanto en el init como en super

class MACD_Chatgpt4(Abstract_Strategy):
    """
    MACD Strategy implementation.
    Inherits from Abstract_Strategy class.
    """

    def __init__(self, parameters: dict, id_strategy: int = None, callback: callable = None
                 , set_basic: bool = True):
        """
        Constructor to initialize MACDStrategy class.

        :param parameters: Dictionary containing parameters for the strategy.
        :param id_strategy: Unique identifier for the strategy.
        :param callback: Callback function.
        """
        # Initialize the base class
        super().__init__(parameters, id_strategy, callback, set_basic)

        # Initialize additional parameters specific to MACD
        self.short_window = parameters['short_window']
        self.long_window = parameters['long_window']

        # Preallocate memory for storing past events
        self.close_prices = []

    def calculate_MACD(self, close_prices: list) -> float:
        """
        Method to calculate MACD

        :param close_prices: List of close prices.
        :return: MACD value.
        """
        short_avg = sum(close_prices[-self.short_window:]) / self.short_window
        long_avg = sum(close_prices[-self.long_window:]) / self.long_window
        return short_avg - long_avg

    def add_event(self, event: dataclass):
        """
        Override the add_event method to implement MACD strategy.

        :param event: Event data.
        """
        if event.event_type == 'bar':
            # Update the internal state
            self.close_prices.append(event.close)

            # Ensure we have enough data to calculate MACD
            if len(self.close_prices) >= self.long_window:

                # Calculate MACD
                macd_value = self.calculate_MACD(self.close_prices)

                # Send orders based on MACD
                if macd_value > 0 and self.position <= 0:  # MACD above zero and no long position
                    self.send_order(price=event.close, quantity=self.quantity, action='buy',
                                    type='market', datetime=event.datetime, ticker=self.ticker)
                    self.position = 1

                elif macd_value < 0 and self.position >= 0:  # MACD below zero and no short position
                    self.send_order(price=event.close, quantity=self.quantity, action='sell',
                                    type='market', datetime=event.datetime, ticker=self.ticker)
                    self.position = -1
        elif event.event_type == 'tick' and event.tick_type == 'close_day':
            self.update_equity(event)


