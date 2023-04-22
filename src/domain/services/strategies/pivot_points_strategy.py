from src.domain.abstractions.abstract_strategy import Abstract_Strategy
from typing import Dict
import numpy as np


class Pivot_Points_Strategy(Abstract_Strategy):
    def __init__(self, parameters: dict = None, id_strategy: int = None, callback: callable = None,
                 set_basic: bool = True):
        super().__init__(parameters, id_strategy, callback, set_basic)
        
        # Initialize variables
        self.high = None
        self.low = None
        self.close = None
        self.pivot_point = None
        self.support_1 = None
        self.resistance_1 = None
        self.support_2 = None
        self.resistance_2 = None

    def calculate_pivot_points(self):
        # Calculate the pivot point
        self.pivot_point = (self.high + self.low + self.close) / 3
        # Calculate the support and resistance levels
        self.support_1 = 2 * self.pivot_point - self.high
        self.resistance_1 = 2 * self.pivot_point - self.low
        self.support_2 = self.pivot_point - (self.high - self.low)
        self.resistance_2 = self.pivot_point + (self.high - self.low)

    def add_event(self, event):
        if event.event_type == 'bar':
            # Store high, low, and close prices
            self.high = event.high
            self.low = event.low
            self.close = event.close
            
            # Calculate pivot points
            self.calculate_pivot_points()
            
            # Counter-trend trading logic
            if self.close >= self.resistance_2 and self.position <= 0:
                quantity = self.quantity
                if self.position == 1:
                    quantity = self.quantity * 2
                
                # Send a sell order
                self.send_order(ticker=self.ticker, price=event.close, quantity=quantity, action='sell',
                                type='market', datetime=event.datetime)
            elif self.close <= self.support_2 and self.position >= 0:
                quantity = self.quantity
                if self.position == 1:
                    quantity = self.quantity * 2
                
                # Send a buy order
                self.send_order(ticker=self.ticker, price=event.close, quantity=quantity, action='buy',
                                type='market', datetime=event.datetime)
        elif event.event_type == 'tick' and event.tick_type == 'close_day':
            # Update equity strategy at the end of the day if necessary
            self.update_equity(event)
