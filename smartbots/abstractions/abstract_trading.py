from abc import ABC
import dataclasses
import datetime as dt
from typing import Dict, List



class Abstract_Trading(ABC):
    """ Abstract class for financial Broker or conectivity with crypto exchange
    All brokers must inherit from this class"""
    def __init__(self,send_orders_status: bool = True, exchange_or_broker=''):
        self.exchange_or_broker = exchange_or_broker
        self.client = self.get_client()
        # variables of orders status
        self.dict_open_orders = {}  # key is the order_id_sender, open order in the broker
        self.dict_cancel_and_close_orders = {}  # key is the order_id_sender, closed or cancelled order in the broker
        self.dict_from_strategies = {}  # key is order_id_sender from strategies, before send to broker or with error
        self.send_orders_status = send_orders_status


    def get_client(self):
        # to be implemented in the child class
        pass
    def get_historical_data(self, timeframe: str = '1m', limit: int = 2, start_date: dt.datetime = None,
                            end_date: dt.datetime = dt.datetime.utcnow(),
                            symbols: List[str] = ['BCT-USDC']) -> List[Dict]:
        """Return historical data on freq for a list of symbols.
        Parameters
        ----------
        timeframe: str (default: '1m')
        limit: int (default: 2, last ohlcv)
        start_date: datetime (default: None)
        end_date: datetime (default: now)
        symbols of the assets. Example: BTC-USDT, ETH-USDT, etc.
        """
        # to be implemented in the child class
        pass

    def start_update_orders_status(self) -> None:
        """Start update orders status."""
        # to be implemented in the child class
        pass

    def send_order(self, order: dataclasses.dataclass) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        # to be implemented in the child class
        pass

    def cancel_order(self, order: dataclasses.dataclass) -> None:
        """Cancel order.

        Parameters
        ----------
        order: event order
        """
        # to be implemented in the child class
        pass

    def get_info_order(self, order: dataclasses.dataclass) -> None:
        """Get fills.

        Parameters
        ----------
        order: event order
        """
        # to be implemented in the child class
        pass

    def get_total_balance(self, currency: str = 'USDT') -> float:
        """Get total balance.

        Parameters
        ----------
        currency: str (default: 'USDT')
        """
        # to be implemented in the child class
        pass


    def get_account_positions(self):
        """
           Account positions
        """
        # to be implemented in the child class
        pass

    def close_all_positions(self):
        """
        Close all positions.
        """
        # to be implemented in the child class
        pass

    def get_stream_quotes_changes(self, tickers :list, callback=None):

        """
        :param tickers, list of ticker
        :param callback function to call when a ticker changes
        :return:
        """
        # to be implemented in the child class
        pass


    def get_trades(self) -> Dict:
        """
           Returns open trades
        """
        # to be implemented in the child class
        pass





