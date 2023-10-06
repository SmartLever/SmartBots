# errores: en el init no ha puesto estos parametros: id_strategy: int = None,
# callback: callable = None, set_basic: bool = True, asi como en el super(), no inicializo la varialble self.closes el cual era una lista,
# n diferencio entre las diferentes tipos de evetntos, importo mal Abstract_Strategy, la logica de insertar datos en el self.closes estaba mal implementada.
# el calculo del macd tambien estaba mal, asi que al final tuve que reucrrir al chatgpt y a la primera me dio las correciones necesarias

from dataclasses import dataclass
from src.domain.abstractions.abstract_strategy import Abstract_Strategy, Order
import datetime as dt


class MACD_Perplexity(Abstract_Strategy):
    """
    MACD Strategy Implementation
    """

    def __init__(self, parameters: dict, id_strategy: int = None, callback: callable = None,
                 set_basic: bool = True):
        super().__init__(parameters, id_strategy, callback, set_basic)

        # MACD parameters
        self.short_period = parameters['short_period']
        self.long_period = parameters['long_period']
        self.signal_period = parameters['signal_period']

        # Initialize MACD and Signal line as empty lists
        self.macd = []
        self.signal = []

        # Preallocate memory for close prices
        self.closes = []

    def calculate_macd(self, closes):
        """
        Calculate MACD and Signal line.
        """
        ema_short = self.ema(closes[-self.short_period:], self.short_period)
        ema_long = self.ema(closes[-self.long_period:], self.long_period)

        # Calculate MACD
        self.macd.append(ema_short[-1] - ema_long[-1])

        # Calculate Signal line
        if len(self.macd) >= self.signal_period:
            self.signal.append(self.ema(self.macd[-self.signal_period:], self.signal_period)[-1])

    def ema(self, data, period):
        """
        Calculate Exponential Moving Average (EMA).
        """
        alpha = 2 / (period + 1)
        ema = [sum(data[:period]) / period]

        for price in data[period:]:
            ema.append((price * alpha) + (ema[-1] * (1 - alpha)))

        return ema

    def add_event(self, event: dataclass):
        """
        Handle new market data events and apply strategy logic.
        """
        if event.event_type == 'bar':
            # Store close prices
            self.closes.append(event.close)

            # Only calculate MACD if we have enough data
            if len(self.closes) >= self.long_period:
                self.calculate_macd(self.closes)

            # Check MACD and Signal line to send orders
            if len(self.macd) > 0 and len(self.signal) > 0:
                if self.macd[-1] > self.signal[-1] and self.position != 1:
                    self.send_order(ticker=self.ticker, price=event.close, quantity=self.quantity,
                                    action='buy', type='market', datetime=event.datetime)
                    self.position = 1  # Update position to Long

                elif self.macd[-1] < self.signal[-1] and self.position != -1:
                    self.send_order(ticker=self.ticker, price=event.close, quantity=self.quantity,
                                    action='sell', type='market', datetime=event.datetime)
                    self.position = -1  # Update position to Short

        elif event.event_type == 'tick' and event.tick_type == 'close_day':
            self.update_equity(event)

