from src.domain.abstractions.abstract_strategy import Abstract_Strategy
import pandas as pd
from dataclasses import dataclass
#  bard me dio 3 versiones, eliji la ultima que era las que mas se adaptaba, la informacion se vera en el enlace, errores: no ha importado el dataclass, podria haber puesto un valor por defecto a los parametros parq que sea mas intuitivo,
# cuando enviar la orden deberia cambiar el valor de
# # self.position para que no envie multiples ordenes
# en el metodo add_event no diferencia entre bar or tick, ademas de faltarle cuando sea el close_day actualizar la equities, tendria que diferenciar porque va a dar
# errores, a la hora de calcullar  en el metodo calculate_macd, bard no me dio la respues correcta en ningun momento, le pase varios fallos y no termino de arregarlo
# al final tuve que utilizar chatgpt para que me aydara y me corregio el codigo


class MACD_Bard(Abstract_Strategy):
    """
    MACD Strategy

    This strategy buys the asset when the short-period MACD is greater than the long-period MACD
    and sells the asset when the long-period MACD is greater than the short-period MACD.

    Parameters:
        fast_period: The fast period of the MACD. Default is 12.
        slow_period: The slow period of the MACD. Default is 26.
        signal_period: The signal period of the MACD. Default is 9.
    """

    def __init__(self, parameters: dict = None, id_strategy: int = None,
                 callback: callable = None, set_basic: bool = True):

        super().__init__(parameters, id_strategy, callback, set_basic)

        # MACD parameters with default values
        self.fast_period = parameters.get('fast_period', 12)
        self.slow_period = parameters.get('slow_period', 26)
        self.signal_period = parameters.get('signal_period', 9)

        # MACD variables
        self.macd = []
        self.signal_line = []
        self.close_prices = []

    def calculate_macd(self, close: float):
        """
        Calculates the MACD.

        Parameters:
            close: The close price.
        """

        self.close_prices.append(close)

        if len(self.close_prices) >= self.slow_period:
            fast_ema = sum(self.close_prices[-self.fast_period:]) / self.fast_period
            slow_ema = sum(self.close_prices[-self.slow_period:]) / self.slow_period

            self.macd.append(fast_ema - slow_ema)

            if len(self.macd) >= self.signal_period:
                self.signal_line.append(sum(self.macd[-self.signal_period:]) / self.signal_period)

    def add_event(self, event: dataclass):
        """
        Adds an event to the strategy.

        Parameters:
            event: The event data.
        """
        if event.event_type == 'bar':
            # Calculate the MACD
            self.calculate_macd(event.close)

            if len(self.signal_line) > 0:
                # Check if the MACD is crossing the signal line
                if self.macd[-1] > self.signal_line[-1] and self.position != 1:
                    # Buy the asset
                    self.send_order(ticker=event.ticker, price=event.close, quantity=self.quantity,
                                    action='buy', type='market', datetime=event.datetime)
                    self.position = 1

                elif self.macd[-1] < self.signal_line[-1] and self.position != -1:
                    # Sell the asset
                    self.send_order(ticker=event.ticker, price=event.close, quantity=self.quantity,
                                    action='sell', type='market', datetime=event.datetime)
                    self.position = -1

        elif event.event_type == 'tick' and event.tick_type == 'close_day':
            self.update_equity(event)