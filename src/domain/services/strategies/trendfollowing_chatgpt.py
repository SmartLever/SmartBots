from src.domain.abstractions.abstract_strategy import Abstract_Strategy
from typing import Dict
import numpy as np


class TrendFollowing_ChatGpt(Abstract_Strategy):
    def __init__(self, parameters: dict = None, id_strategy: int = None, callback: callable = None,
                 set_basic: bool = True):
        super().__init__(parameters, id_strategy, callback, set_basic)
        self.buffer = []
        self.pattern_length = 3
        self.short_ma_period = 50
        self.long_ma_period = 200
        if 'pattern_length' in self.parameters:
            self.pattern_length = self.parameters['pattern_length']
        if 'short_ma_period' in self.parameters:
            self.short_ma_period = self.parameters['short_ma_period']
        if 'long_ma_period' in self.parameters:
            self.long_ma_period = self.parameters['long_ma_period']
        self.short_ma = None
        self.long_ma = None

    def calculate_moving_averages(self, event):
        if len(self.buffer) > self.long_ma_period:
            self.buffer.pop(0)
        if len(self.buffer) >= self.short_ma_period:
            self.short_ma = sum(self.buffer[-self.short_ma_period:]) / self.short_ma_period
            self.long_ma = sum(self.buffer[-self.long_ma_period:]) / self.long_ma_period

    def add_event(self, event):
        if event.event_type == 'bar':
            self.buffer.append(event.close)
            self.n_events += 1
            self.calculate_moving_averages(event)
            if self.n_events > self.long_ma_period:
                if self.short_ma > self.long_ma:
                    if self.position <= 0:
                        if self.check_pattern():
                            self.send_order(ticker=self.ticker, price=event.close, quantity=self.quantity, action='buy',
                                            type='market', datetime=event.datetime)
                elif self.short_ma < self.long_ma:
                    if self.position >= 0:
                        if self.check_pattern():
                            self.send_order(ticker=self.ticker, price=event.close, quantity=self.quantity, action='sell',
                                            type='market', datetime=event.datetime)

        elif event.event_type == 'tick' and event.tick_type == 'close_day':
            self.update_equity(event)

    def check_pattern(self):
        if len(self.buffer) >= self.pattern_length:
            pattern = self.buffer[-self.pattern_length:]
            trend = pattern[-1] > pattern[0]
            for i in range(1, len(pattern)):
                if (trend and pattern[i] < pattern[i - 1]) or (not trend and pattern[i] > pattern[i - 1]):
                    return False
            if (trend and pattern[-1] > pattern[-2]) or (not trend and pattern[-1]  < pattern[-2]):
                return True
        return False