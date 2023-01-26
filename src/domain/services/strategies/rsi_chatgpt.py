from src.domain.abstractions.abstract_strategy import Abstract_Strategy
from typing import Dict
import numpy as np


class RSI_Chatgpt(Abstract_Strategy):
    def __init__(self, parameters: dict = None, id_strategy: int = None, callback: callable = None,
                 set_basic: bool = True):
        """
        You are a specialized Python coding assistant for quantitative trading with trading systems and strategies. Using the following 18 guidelines,
        create a new class that inherits from the Abstract_Strategy class and implement the next request:
          " YOUR REQUEST "
        1. Import the Abstract_Strategy class from **`src.domain.abstractions.abstract_strategy`**
        2. Create a new class that inherits from Abstract_Strategy.
        3. Use methods and functions to encapsulate the calculation of any indicator and algorithm from the request.
        4. Override the add_event method and implement the algorithms and indicators from the request.
        5. Avoid using third-party libraries for indicators, instead develop your own methods.
        6. Do not use callbacks in the add_event method.
        7. Include detailed comments in the code to explain the methods, functions and classes.
        8. Use the self.ticket, price, self.quantity, action, type, and datetime arguments when calling the send_order method.
        9. Event received in the add_event method is a dataclass type, with attributes for close, open, high, low, volume, and ticker.
        10. Provide a dictionary of inputs for any indicator you create from the request in the `parameters` argument from init method.
        11. When conditions for buying and selling are met, use the send_order method with keyword arguments.
        12. When conditions for buying and selling are met, only send one order until the strategy change.
        13. Use event.event_type checking, it can be ‘bar’ and ‘tick’ type.
        14. Use self.position and do not change value of self.position in add_event method. send_order method calculate self.number_of_contracts variable that you have to use in send_order implementation.
        15. Preallocate memory to avoid storing more data than necessary with variables.
        16. Refer to past events to calculate variable if the request is not expressed in another way.
        17. Use _add_event_example as an example for implement add_event.
        18. Create an answer within one code block.

        Context:  Copy Code from https://github.com/SmartLever/SmartBots/blob/main/src/domain/abstractions/abstract_strategy.py """


        super().__init__(parameters, id_strategy, callback, set_basic)
        self.previous_close = None
        self.rsi_period = 14
        if 'rsi_period' in self.parameters:
            self.rsi_period = self.parameters['rsi_period']
        self.gain = 0
        self.loss = 0
        self.average_gain = 0
        self.average_loss = 0
        self.previous_change = 0
        self.rsi = None

    def calculate_rsi(self, event):
        close = event.close
        if self.previous_close is None:
            self.previous_close = close
        change = close - self.previous_close
        self.previous_close = close
        if self.n_events <= self.rsi_period:
            if change > 0:
                self.gain += change
            else:
                self.loss -= change
            if self.n_events == self.rsi_period:
                self.average_gain = self.gain / self.rsi_period
                self.average_loss = self.loss / self.rsi_period
        else:
            if change > 0:
                self.average_gain = ((self.average_gain * (self.rsi_period - 1)) + change) / self.rsi_period
                self.average_loss = ((self.average_loss * (self.rsi_period - 1)) + 0) / self.rsi_period
            else:
                self.average_gain = ((self.average_gain * (self.rsi_period - 1)) + 0) / self.rsi_period
                self.average_loss = ((self.average_loss * (self.rsi_period - 1)) - change) / self.rsi_period
        if self.average_loss != 0:
            self.rsi = 100 - (100 / (1 + (self.average_gain / self.average_loss)))

    def add_event(self, event):
        if event.event_type == 'bar':
            self.n_events += 1
            self.calculate_rsi(event)
            if self.n_events > self.rsi_period:
                if self.rsi > 80 and self.position <= 0:
                    quantity = self.quantity
                    if self.position == 1:
                        quantity = self.quantity * 2

                    self.send_order(ticker=self.ticker, price=event.close, quantity=quantity, action='buy',
                                    type='market', datetime=event.datetime)
                elif self.rsi < 20 and self.position >= 0:
                    quantity = self.quantity
                    if self.position == 1:
                        quantity = self.quantity * 2
                    self.send_order(ticker=self.ticker, price=event.close, quantity=quantity, action='sell',
                                    type='market', datetime=event.datetime)

        elif event.event_type == 'tick' and event.tick_type == 'close_day':
            """Logic of the Strategy goes here for calculate data at the end of the day if it was necessary"""
            # update equity strategy
            self.update_equity(event)