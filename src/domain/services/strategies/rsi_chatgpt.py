from dataclasses import dataclass
from src.domain.abstractions.abstract_strategy import Abstract_Strategy
import math

class RSI_Chatgpt(Abstract_Strategy):
    """ Strategy RSI_Strategy  using  Basic_Strategy as base class
        Create with CHATGPT with this prompt:

        You are a brilliant and helpful Python coding assistant specialized in quantitative trading with trading systems or strategies, designed to help users. Use the next points:

        - Your context will be the abstract class name Abstract_Strategy.
        - Locate context under the word CONTEXT and between “”” “””, you can import it from:  `from src.domain.abstractions.abstract_strategy import Abstract_Strategy`
        - Create a new class that inherit form Abstract_Strategy.
        - Modified the new class to accomplish the request.
        - Create new methods to encapsulate the calculus of indicator and algorithm from the request.
        - Overrides the add_event method and implements the request.
        - Implement methods and functions created in add_event.
        - Taker into account the event  receive in add_event method is a dataclass type: `from dataclasses import dataclass`, the attributes for the event will be close, open, high, low, volumen, ticker from stocks and futures data.
        - Avoid using third-party libraries for indicators; instead, develop your own methods.
        - Do not use `callback` in add_event method.
        - Create comments that explain the code, and strive for clear, concise code.
        - When the conditions are met for buying and selling, use the `send_order` method. Pass the following arguments to it: `self.ticker`, `price`, `self.quantity`, `action`, `type`, and `datetime.` Do not override it.
        - Create an answer within one code block.

        My first request is:  I want a strategy that applies the Relative Strength Index (RSI). If the RSI is greater than 80, it should send a sell order, and if the RSI is less than 20, it should send a buy order.
        CONTEXT:
        src/domain/abstractions/abstract_strategy.py
    """
    def __init__(self, parameters: dict = None, id_strategy: int = None, callback: callable = None, set_basic: bool = True):
        super().__init__(parameters, id_strategy, callback, set_basic)
        self.gain_loss_vector = []
        self.average_gain = 0
        self.average_loss = 0
        self.rsi = 0
        self.prev_close = 0
        self.period = 14
        if 'period' in parameters:
            self.period = parameters['period']

    def calculate_gain_loss(self, close: float):
        change = close - self.prev_close
        self.prev_close = close
        if change > 0:
            return change
        else:
            return -change

    def calculate_rsi(self):
        if self.average_loss == 0:
            self.rsi = 100
        else:
            self.rsi = 100 - (100 / (1 + (self.average_gain / self.average_loss)))

    def add_event(self, event: dataclass):
        self.n_events += 1
        self.gain_loss_vector.append(self.calculate_gain_loss(event.close))
        if len(self.gain_loss_vector) > self.period:
            self.gain_loss_vector.pop(0)
        if self.n_events > self.period:
            self.average_gain = sum(x for x in self.gain_loss_vector if x > 0) / self.period
            self.average_loss = abs(sum(x for x in self.gain_loss_vector if x < 0) / self.period)
            self.calculate_rsi()
            if self.rsi > 80:
                self.send_order(ticker=self.ticker, price=event.close, quantity=self.quantity,
                                action='Sell',  type='Market', datetime=event.datetime)
            elif self.rsi < 20:
                self.send_order(ticker=self.ticker, price=event.close, quantity=self.quantity,
                                action='Buy',  type='Market', datetime=event.datetime)