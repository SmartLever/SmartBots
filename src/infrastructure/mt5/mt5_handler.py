import dataclasses
from typing import Dict, List
import threading
import time
import datetime as dt
from src.domain.abstractions.abstract_trading import Abstract_Trading
from src.domain.decorators import check_api_key
from src.infrastructure.mt5.mt5_zeromq_connector import Metatrader
from src.application.base_logger import logger
from src.infrastructure.brokerMQ import Emit_Events


@check_api_key(
    [
        "MT5_HOST",
    ]
)
def get_client(conf_port):
    """Get MT5 client.

    Returns
    -------
    Client
        MT5 client.
    """
    logger.info("Connecting to MT5")
    client = Metatrader(host=conf_port['MT5_HOST'], type_service=conf_port['type_service'])

    return client


class Trading(Abstract_Trading):
    """Class for trading on MT5.

    Attributes
    ----------
    client: Client
         MT5 client.
    """

    def __init__(self, send_orders_status: bool = True, exchange_or_broker='darwinex_broker', config_broker: Dict = {},
                 config_brokermq: Dict = {}) -> None:
        """Initialize class."""

        type_service = exchange_or_broker.split('_')[2]
        config_port = {'MT5_HOST': config_broker['MT5_HOST'], 'type_service': type_service}
        self.config_port = config_port
        super().__init__(send_orders_status=send_orders_status, exchange_or_broker=exchange_or_broker,
                         config_broker=config_broker)
        self.exchange_or_broker = exchange_or_broker.split('_')[0]
        self.dwt = None  # darwinex_ticks with FTP connection
        self.sleep = None
        if self.send_orders_status:
            self.emit_orders = Emit_Events(config=config_brokermq)
        else:
            self.emit_orders = None

    def get_client(self):
        return get_client(self.config_port)

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
    
    def send_order(self, order: dataclasses.dataclass):
        """
        Send Normal order or close trade
        Parameters
        ----------
        order: event order
        """

        if order.action_mt4 == 'normal':
            self._send_order_normal(order)

        else:
            if order.action_mt4 == 'close_trade':
                # Close total
                logger.info(f'Sending Order to close positions in ticker: {order.ticker} quantity: {order.quantity}')
                respond_order = self.client.CloseById(order.order_id_receiver)

            # partially closed trade
            elif order.action_mt4 == 'close_partial':
                logger.info(f'Sending Order to close partial positions in ticker: {order.ticker} quantity: {order.quantity}')

                respond_order = self.client.ClosePartial(order.order_id_receiver, order.quantity)

            try:
                # Saving order_id en order
                print(respond_order)
                order.order_id_receiver = str(respond_order['order'])
                if respond_order['error'] is False:
                    logger.info(f'order closes successfully in ticker: {order.ticker} quantity: {order.quantity}'
                                f' with id: {order.order_id_receiver}')
                    order.status = 'closed'
                    order.filled_price = float(respond_order['price'])
                    quantity_execute = respond_order['volume']
                    order.quantity_execute = quantity_execute
                    order.quantity_left = order.quantity - quantity_execute

                else:  # error
                    logger.error(f'Error in order in ticker: {order.ticker} quantity: {order.quantity}'
                                 f' with id: {order.order_id_receiver}')
                    order.status = 'error'

            except Exception as ex:
                logger.error(f'Error in close order in ticker: {order.ticker} quantity: {order.quantity} Exception: {ex}')
                order.status = 'error'
                order.error_description = str(ex)
                print(ex)

            if order.status == "error":
                print(f'Error sending order {order}')
                if self.send_orders_status:  # publish order status with error
                    self.emit_orders.publish_event('order_status', order)

            else:
                # eliminate from dict_from_strategies and create it in dict_open_orders
                if order.order_id_sender in self.dict_from_strategies:
                    self.dict_from_strategies.pop(order.order_id_sender)
                if order.order_id_sender in self.dict_open_orders:
                    self.dict_open_orders[order.order_id_sender] = order

    def get_account_positions(self):
        """
           Account positions
        """
        try:
            sign = {'POSITION_TYPE_BUY': 1, 'POSITION_TYPE_SELL': -1}
            positions = {}
            open_trades = self.client.positions()
            if 'positions' in open_trades:
                open_trades = open_trades['positions']
            for trade in open_trades:
                symbol = trade['symbol']
                try:
                    positions[symbol] = positions[symbol] + sign[trade[
                        'type']] * trade['volume']
                except KeyError:
                    positions[symbol] = sign[trade['type']] * \
                                        trade['volume']

            return positions
        except:
            return None

    def get_trades(self) -> Dict:
        try:
            open_trades = self.client.positions()
        except:
            open_trades=None

        return open_trades
    def close_all_positions(self):
        """
        Close all positions.
        """
        self.client.close_all()

    def get_stream_quotes_changes(self, tickers, timeframe, callback):

        """
        :param tickers, list of ticker
        :param timeframe:
        :return:
        """
        self.client.price(tickers, timeframe, callback)


    def get_total_balance(self, _delay=0.1, _wbreak=10):
        """
        Get Balance
        """
        response = self.client.balance()

        if response is None:
            msg = 'No response received, either there are no open trades or check the connection'
            logger.error(msg)
            print(msg)
            return None
        else:
            return response['equity']

    def _send_order_normal(self, order: dataclasses.dataclass):
        """
        Send Normal order
        Parameters
        ----------
        order: event order
        """
        logger.info(f'Sending Order to MT5 in ticker: {order.ticker} quantity: {order.quantity}')
        self.dict_from_strategies[order.order_id_sender] = order  # save order in dict_from_strategies
        try:
            order_response = self._send_order(order)

            print(f'Response order :{order_response}')
            if order_response:
                # Saving order_id in order
                order.order_id_receiver = str(order_response['order'])

                if order_response['error'] is False:
                    logger.info(f'order executed successfully in ticker: {order.ticker} quantity: {order.quantity} '
                                f'with id: {order.order_id_receiver}')
                    order.datetime_in = dt.datetime.utcnow()
                    order.status = "open"
                    order.filled_price = order_response['price']
                    order.quantity_execute =  order_response['volume']

                else:  # error
                    logger.error(
                        f'Error in order in ticker: {order.ticker} quantity: {order.quantity} with id: '
                        f'{order.order_id_receiver}')
                    order.order_status = 'error'
        except Exception as ex:
            logger.error(
                f'Error in order in ticker: {order.ticker} quantity: {order.quantity} Exception: {ex}')
            order.order_status = 'error'
            print(ex)
            order.status = "error"
            order.error_description = str(ex)

        if order.status == "error":
            print(f'Error sending order {order}')
            if self.send_orders_status:  # publish order status with error
                self.emit_orders.publish_event('order_status', order)

        else:
            # eliminate from dict_from_strategies and create it in dict_open_orders
            self.dict_from_strategies.pop(order.order_id_sender)
            self.dict_open_orders[order.order_id_sender] = order

    def _send_order(self, order: dataclasses.dataclass):
        try:
            if order.type in ['market']:
                if order.action == 'buy':
                    # symbol, volume, stoploss, takeprofit, deviation
                    response = self.client.buy(order.ticker, order.quantity, 0, 0, 0)
                elif order.action == 'sell':
                    # symbol, volume, stoploss, takeprofit, deviation
                    response = self.client.sell(order.ticker, order.quantity, 0, 0, 0)
            elif order.type in ['limit']:
                if order.action == 'buy':
                    # symbol, volume, stoploss, takeprofit, price, deviation
                    response = self.client.buyLimit(order.ticker, order.quantity, 0, 0, order.price, 0)
                elif order.action == 'sell':
                    # symbol, volume, stoploss, takeprofit, price, deviation
                    response = self.client.sellLimit(order.ticker, order.quantity, 0, 0, order.price, 0)


            return response
        except:
            return {'order': None, 'error': True}

    def _check_order(self):
        """ Check open order and send changes to Portfolio  and for saving in the database"""
        current_positions = self.get_account_positions()
        list_changing = []
        for order_id in self.dict_open_orders.keys():
            order = self.dict_open_orders[order_id]
            # check if this order is open
            order_id_receiver = int(order.order_id_receiver)
            if order_id_receiver in current_positions:
                order.status = 'open'
                info_order = current_positions[int(order.order_id_receiver)]
                if '_open_price' in info_order:
                    order.filled_price = info_order['_open_price']
                quantity_execute = info_order['_lots']
                order.quantity_execute = quantity_execute
                order.quantity_left = order.quantity - quantity_execute
            else:
                order.status = 'closed'

            if order.status == 'closed' or order.status == 'cancelled':
                list_changing.append(order_id)
            if self.send_orders_status:  # publish order status
                order.datetime = dt.datetime.utcnow()
                self.emit_orders.publish_event('order_status', order)

        for order_id in list_changing:
            # eliminate from dict_open_orders and create in dict_cancel_and_close_orders
            self.dict_open_orders.pop(order_id)
            self.dict_cancel_and_close_orders[order_id] = order
