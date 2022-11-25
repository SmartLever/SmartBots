""" DOCS: https://github.com/ccxt/ccxt/wiki/Manual#markets """

from src.domain.abstractions.abstract_trading import Abstract_Trading
import dataclasses
from typing import Dict, List
import time
import pandas as pd
import datetime as dt
from src.infraestructure.brokerMQ import Emit_Events
import os
import ccxt
import threading
from src.application.base_logger import logger
print('CCXT Version:', ccxt.__version__)


# default Callable
async def _callable(data: Dict) -> None:
    """Callback function for realtime data. [Source: Crypto Exchange]

    Parameters
    ----------
    data: Dict
        Realtime data.
    """
    print(data)


# Decorator for checking API key
def get_client(exchange: str = 'kucoin'):
    """Get Crypto Exchange client.

    Returns
    -------
    Client
        Crypto Exchange client.
    """
    # Get API key
    api_key = os.environ.get(f'API_{exchange.upper()}_API_KEYS')
    password = os.environ.get(f'API_{exchange.upper()}_API_PASSPHRASE')
    secret = os.environ.get(f'API_{exchange.upper()}_API_SECRET')
    uid = os.environ.get(f'API_{exchange.upper()}_API_UID')
    if api_key is None:
        logger.warning(f'API key for {exchange} is not set. You have to set API key in conf.env file and compose.env.')
        api_key = ''
    if password is None:
        password = ''
    if secret is None:
        secret = ''
    if uid is not None:
        uid = ''
    return getattr(ccxt,exchange)({'apiKey': api_key,'password': password,
                                   'secret': secret,'uid': uid,
                                   'enableRateLimit': True})


class Trading(Abstract_Trading):
    """Class for trading on Kucoin.

    Attributes
    ----------
    client: Client
        Exchange client.
    """

    def __init__(self, send_orders_status: bool = True, exchange_or_broker='kucoin', config_brokermq: Dict = {}) -> None:
        """Initialize class."""
        super().__init__(send_orders_status=send_orders_status, exchange_or_broker=exchange_or_broker,
                         config_brokermq=config_brokermq)
        self.exchange_or_broker = exchange_or_broker
        self.client = self.get_client()

        if self.send_orders_status:
            self.emit_orders = Emit_Events(config=config_brokermq)
        else:
            self.emit_orders = None

    def get_client(self):
        return get_client(exchange=self.exchange_or_broker)

    def get_historical_data(self, timeframe:str ='1m', limit: int = 2, start_date: dt.datetime = None,
                            end_date: dt.datetime = dt.datetime.utcnow(),
                            symbols: List[str] = ['BCT-USDC']) -> List[Dict]:
        """Return realtime data on freq for a list of symbols.
        Parameters
        ----------
        exchange: str (default: 'kucoin')
        timeframe: str (default: '1m')
        limit: int (default: 2, last ohlcv)
        since: from timestamp (default: None)
        setting: dict (default: {'symbols': List[str]})
            Symbols of the assets. Example: BTC-USDT, ETH-USDT, etc.
        """
        def get_ohlcv_last(symbol, timeframe):
            ohlcv = self.client.fetch_ohlcv(symbol, timeframe, None, 2)
            if len(ohlcv):
                first_candle = ohlcv[0]
                datetime = self.client.iso8601(first_candle[0])
                return {'datetime': datetime, 'exchange': self.client.id, 'symbol': symbol,
                                 'candle': first_candle}

        def get_ohlcv(symbol, timeframe, limit=1500,since=None):
            ohlcv = self.client.fetch_ohlcv(symbol, timeframe, since, limit)
            if len(ohlcv):
                return ohlcv

        if type(symbols) is str:
            symbols = [symbols]
        bars = []
        if limit == 2: # last ohlcv
            for symbol in symbols:
                    try:
                        bars.append(get_ohlcv_last(symbol, timeframe))
                    except Exception as e:
                        print(type(e).__name__, str(e))
                        time.sleep(0.1)
                        bars.append(get_ohlcv_last(symbol, timeframe))
            return bars
        else: # historical data
            bars = {s: [] for s in symbols}
            for symbol in symbols:
                _to_date = self.client.parse8601(str(end_date))  # milliseconds
                _since = self.client.parse8601(str(start_date))
                keep_going = True
                while keep_going:
                    try:
                        _df = get_ohlcv(symbol, timeframe, limit=1500, since=_since)
                        if _df is not None:
                            df = pd.DataFrame(_df, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
                            df.index = pd.to_datetime(df['datetime'], unit='ms')
                            df['symbol'] = symbol
                            df['exchange'] = self.exchange_or_broker
                            bars[symbol].append(df)
                            _since = _df[-1][0] + 60000 # 1 min
                            print(f'{symbol} Since: {self.client.iso8601(_since)}')
                            if _since >= _to_date:
                                keep_going = False
                        if _df is None and timeframe != '1m':
                            keep_going = False
                    except Exception as e:
                        print(type(e).__name__, str(e))
                        time.sleep(1)
            if len(bars) > 0:
                return {s: pd.concat(bars[s]) for s in symbols if s in bars}
            else:
                return {}

    def start_update_orders_status(self) -> None:
        """Start update orders status."""

        def run_status_orders():
            while True:
                try:
                    if len(self.dict_open_orders) > 0:  # if there are open orders
                        self._check_order()
                        time.sleep(30)
                    else:
                        time.sleep(1)
                except Exception as ex:
                    logger.error(
                        f'Error check_order Exception: {ex}')

        x = threading.Thread(target=run_status_orders)
        x.start()

    def send_order(self, order: dataclasses.dataclass) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        logger.info(f'Sending Order to {self.exchange_or_broker} in ticker: {order.ticker} quantity: {order.quantity}')
        self.dict_from_strategies[order.order_id_sender] = order  # save order in dict_from_strategies
        try:
            self._send_order(order)
        except ConnectionError as e:
            print('ConnectionError, tryin again')
            time.sleep(1)
            self._send_order(order)
        except Exception as e:
            print(e)
            logger.error(
                f'Error in order in ticker: {order.ticker} quantity: {order.quantity} Exception: {e}')
        if order.status == 'error':
            logger.error(
                f'Error sending order in ticker: {order.ticker} quantity: {order.quantity}')
            print(f'Error sending order {order}')
            if self.send_orders_status:  # publish order status with error
                self.emit_orders.publish_event('order_status', order)

        else:
            # eliminate from dict_from_strategies and create it in dict_open_orders
            self.dict_from_strategies.pop(order.order_id_sender)
            self.dict_open_orders[order.order_id_sender] = order

    def _send_order(self, order: dataclasses.dataclass) -> None:
        # place order
        ticker = order.ticker
        action = order.action.lower() # buy or sell
        quantity = order.quantity
        price = order.price
        try:
            if order.type == "market":
                info_order = self.client.create_order(ticker, order.type, action, quantity, price)
                order.order_id_receiver = info_order['info']['orderId']
                order.status = "open"
                order.datetime_in = dt.datetime.utcnow()
            elif order.type == "limit":
                info_order = self.client.create_order(ticker, order.type, action, quantity, price)
                order.order_id_receiver = info_order['info']['orderId']
                order.status = "open"
                order.datetime_in = dt.datetime.utcnow()
            else:
                order.status = "error"
                order.error_description = "Type order not recognized"
                raise ValueError(order.error_description)
            print(f'Send order {order}')
        except Exception as e:
            order.status = "error"
            order.error_description = str(e)
            print(f'Send order {order}')
            raise (e)

    def cancel_order(self, order: dataclasses.dataclass) -> None:
        """Cancel order.

        Parameters
        ----------
        order: event order
        """
        logger.info(f'Cancel order in {order.ticker} with id {order.order_id_receiver}')
        try:
            self._cancel_order(order)
        except ConnectionError as e:
            # check if exception is ConnectionResetError y retry
            time.sleep(1)
            self._cancel_order(order)
        except Exception as e:
            print(e)
            logger.error(f'Error Cancel order in {order.ticker} with id {order.order_id_receiver} error: {e}')

    def _cancel_order(self, order: dataclasses.dataclass) -> None:
        info_order = self.client.cancel_order(order.order_id_receiver)
        if "cancelledOrderIds" in info_order['data']:
            print(f"Order cancelled {order}")
            order.status = "cancelled"

    def get_info_order(self, order: dataclasses.dataclass) -> None:
        """Get fills.

        Parameters
        ----------
        order: event order
        """
        try:
            self._get_info_order(order)
        except ConnectionError as e:
            # check if exception is ConnectionResetError
            time.sleep(1)
            self._get_info_order(order)
        except Exception as e:
            print(f'Error getting FillOrders {e}')
            logger.error(f'Error getting FillOrders {e}')


    def _get_info_order(self, order: dataclasses.dataclass) -> None:
        if order.order_id_receiver is not None:
            fills = self.client.fetch_order(order.order_id_receiver)
            if len(fills) == 0:
                time.sleep(5)
                fills = self.client.fetch_order(order.order_id_receiver)

            if len(fills) > 0:
                quantity_execute = fills['filled']
                average_price = fills['average']
                quantity_left = fills['remaining']
                order.quantity_execute = quantity_execute
                order.quantity_left = quantity_left
                # Get  price by ponderate by sizes
                order.filled_price = average_price
                order.status = fills['status']
                order.commission_fee = float(fills['fees'][0]['cost'])
                order.fee_currency = str(fills['fees'][0]['currency'])

    def _check_order(self):
        """ Check open order and send changes to Portfolio  and for saving in the database"""
        list_changing = []
        for order_id in self.dict_open_orders.keys():
            order = self.dict_open_orders[order_id]
            self.get_info_order(order)
            if order.status == 'closed' or order.status == 'cancelled':
                list_changing.append(order_id)
            if self.send_orders_status: # publish order status
                self.emit_orders.publish_event('order_status', order)
            print(f'Order {order.status} {order}')

        for order_id in list_changing:
            # eliminate from dict_open_orders and create in dict_cancel_and_close_orders
            self.dict_open_orders.pop(order_id)
            self.dict_cancel_and_close_orders[order_id] = order

    def get_total_balance(self, currency: str = 'USDT') -> float:
        """Get total balance.

        Parameters
        ----------
        currency: str
            Currency to get balance

        Returns
        -------
        float
            Total balance
        """
        if currency == 'USDT':
            return self._get_total_balance_usd()
        else:
            raise NotImplementedError

    def _get_total_balance_usd(self):
        """ Get total balance in the Exchange
            :param fiat: optional Fiat code
        """
        balance = self.client.fetch_balance()
        tickers = self.client.fetch_tickers()
        balance_usd = 0
        for currency in balance['total']:
            if balance['total'][currency] > 0 and currency != 'USDT':
                price = tickers[f'{currency}/USDT']['close']
                balance_usd += balance['total'][currency] * price
            elif currency == 'USDT':
                balance_usd += balance['total'][currency]

        return balance_usd

    def close_all_positions(self):
        pass
    
    def get_account_positions(self):
        pass


if __name__ == '__main__':
    """ Test"""
    exchange = 'kucoin'
    from src.domain import events
    import datetime as dt
    n = 1
    quantity = 0.05
    trading = Trading(exchange_or_broker=exchange)

    t = 'ETH-USDC'
    action = 'buy'
    price = 1300
    _type = 'limit'
    order_id_sender =f' {0}_{n}_{dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")}'
    order = events.Order(datetime=dt.datetime.utcnow(),
                         ticker=t, action=action,
                         price=price, quantity=abs(quantity), type=_type, sender_id=0,
                         order_id_sender=order_id_sender)
    order.order_id_receiver = '633eb1b9c0c6bc00019611a2'
    #trading.send_order(order)
    #fills = trading.get_info_order(order)
    print(trading.get_total_balance())

