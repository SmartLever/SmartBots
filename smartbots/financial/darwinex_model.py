import dataclasses
from typing import Dict, List
import threading
from smartbots import conf
import time
import datetime as dt
from smartbots.brokerMQ import Emit_Events
from smartbots.decorators import log_start_end, check_api_key
from smartbots.financial.mt4_connector.mt_zeromq_connector import MTZeroMQConnector
from time import sleep
from smartbots.base_logger import logger


# default Callable
async def _callable(data: Dict) -> None:
    """Callback function for realtime data. [Source: MT4 Darwinex]

    Parameters
    ----------
    data: Dict
        Realtime data.
    """
    print(data)

@check_api_key(
    [
        "DARWINEX_HOST",
        "CLIENT_IF",
        "PUSH_PORT",
    ]
)
def get_client(conf_port):
    """Get MT4 Darwinex client.

    Returns
    -------
    Client
        MT4 client.
    """
    logger.info("Connecting to MT4 Darwinex")
    client = MTZeroMQConnector(host=conf_port['DARWINEX_HOST'],
                               client_id=conf_port['CLIENT_IF'],
                               push_port=conf_port['PUSH_PORT'],
                               pull_port=conf_port['PULL_PORT'],
                               sub_port=conf_port['SUB_PORT'])

    return client


class Trading(object):
    """Class for trading on MT4 Darwinex.

    Attributes
    ----------
    client: Client
        Darwinex client.
    """

    def __init__(self, send_orders_status: bool = True, name='mt4_darwinex', type_service='broker') -> None:
        """Initialize class."""
        self.name = name
        if type_service == 'broker':
            config_port = {'DARWINEX_HOST': conf.DARWINEX_HOST,
                           'CLIENT_IF': conf.CLIENT_IF,
                           'PUSH_PORT':  conf.PUSH_PORT,
                           'PULL_PORT': conf.PULL_PORT_BROKER,
                           'SUB_PORT': conf.SUB_PORT_BROKER}
        elif type_service == 'provider':
            config_port = {'DARWINEX_HOST': conf.DARWINEX_HOST,
                           'CLIENT_IF': conf.CLIENT_IF,
                           'PUSH_PORT': conf.PUSH_PORT,
                           'PULL_PORT': conf.PULL_PORT_PROVIDER,
                           'SUB_PORT': conf.SUB_PORT_PROVIDER}
        self.client = get_client(config_port)
        self._open = True
        self.sleep = None
        self.cola_thread = []
        # variables of status orders
        self.dict_open_orders = {}  # key is the order_id_sender, open order in the broker
        self.dict_cancel_and_close_orders = {}  # key is the order_id_sender, closed or cancelled order in the broker
        self.dict_from_strategies = {}  # key is order_id_sender from strategies, before send to broker or with error
        self.send_orders_status = send_orders_status
        if self.send_orders_status:
            self.emit_orders = Emit_Events()
        else:
            self.emit_orders = None

    def start_update_orders_status(self) -> None:
        """Start update orders status."""
        def run_status_orders():
            while True:
                if len(self.dict_open_orders) > 0:  # if there are open orders
                    self.check_order()
                    time.sleep(30)
                else:
                    time.sleep(1)
        x = threading.Thread(target=run_status_orders)
        x.start()

    def get_response(self, key, _delay=0.1, _wbreak=10):
        """
        Returns active positions, balance
        """
        # Reset data output
        self.client._set_response_(None)

        # Get open trades from MetaTrader
        if key == '_info':
            self.client.MTX_GET_BALANCE_()
        elif key == 't':
            self.client.MTX_GET_POSITION_()
        elif key == '_trades':
            self.client.MTX_GET_ALL_OPEN_TRADES_()

        # While loop start time reference
        _ws = dt.datetime.utcnow()

        # While data not received, sleep until timeout
        while not self.client._valid_response_('zmq'):
            sleep(_delay)
            if (dt.datetime.utcnow() - _ws).total_seconds() > (
                    _delay * _wbreak):
                break

        # If data received, return DataFrame
        if self.client._valid_response_('zmq'):
            _response = self.client._get_response_()
            # print('respuesta :', _response)
            if (key in _response.keys()):
                # len(_response['_trades']) > 0):
                return _response[key]
        return None

    def close(self):
        """
        Disconnect
        :return:
        """
        logger.info("Closing connection to MT4 Darwinex")
        print('Closing connection with API')
        self._open = False
        for thread in self.cola_thread:
            thread.join()

    def get_account_positions(self):
        """
           Account positions
        """
        sign = {0: 1, 1: -1, 2: 0, 3: 0}
        positions = {}
        open_trades = self.get_trades()
        trades_id = list(open_trades.keys())
        for trade in trades_id:
            symbol = open_trades[trade]['_symbol']
            try:
                positions[symbol] = positions[symbol] + sign[open_trades[trade][
                    '_type']] * open_trades[trade]['_lots']
            except KeyError:
                positions[symbol] = sign[open_trades[trade]['_type']] * \
                                    open_trades[trade]['_lots']

        return positions

    def _get_OrderConfirmId(self, account_key, id_generator):
        """
        OrderConfirmId = id_generator +_+  Unix epoch time +_+ AccountKey
        OrderConfirmId:string [ 1 .. 25 ] characters
                                    A unique identifier regarding an order used to prevent duplicates.
                                    Must be unique per API key, per order, per user.
        """
        now = str(dt.datetime.utcnow().timestamp()).split('.')[0]
        order_confirm_id = str(id_generator) + '_' + now + '_' + str(account_key)
        if len(order_confirm_id) > 25:
            order_confirm_id = order_confirm_id[:25]

        return order_confirm_id

    def get_trades(self):
        """
           Returns open trades
        """
        response = self.get_response('t')
        if response is None:
            logger.error('No response received, either there are no open trades or check the connection')
            print('No response received, either there are no open trades or check the connection')
            return None
        open_trades = {k: dict(zip(
            ['_symbol', '_lots', '_type'],
            v
        )
        ) for k, v in response.items()}
        return open_trades

    def send_order_normal(self, order: dataclasses.dataclass, up_date=False):
        """
        Send Normal order
        Parameters
        ----------
        order: event order
        """
        logger.info(f'Sending Order to MT4 in ticker: {order.ticker} quantity: {order.quantity}')
        self.dict_from_strategies[order.order_id_sender] = order  # save order in dict_from_strategies
        try:
            order_response = self._send_order(order,
                                              comment=order.order_id_sender,
                                              _verbose=False,
                                              _delay=0.250,
                                              _wbreak=22,
                                              up_date=up_date)

            print(f'Response order :{order_response}')
            if order_response:
                # Saving order_id in order
                order.order_id_receiver = str(order_response['_ticket'])

                if order_response['_action'] == 'EXECUTION':
                    logger.info(f'order executed successfully in ticker: {order.ticker} quantity: {order.quantity} '
                                f'with id: {order.order_id_receiver}')
                    order.datetime_in = dt.datetime.utcnow()
                    order.status = "open"
                    order.filled_price = float(order_response['_open_price'])

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

    def _send_order(self, order: dataclasses.dataclass, comment='SmartBots_to_MT', _verbose=False, _delay=0.1,
                    _wbreak=10, up_date=False):

        _check = ''
        actions = {'buy': 0,
                   'sell': 1,
                   'limit_buy': 2,
                   'limit_sell': 3,
                   'stop_buy': 4,
                   'stop_sell': 5}
        exec_dict = {'_symbol': order.ticker,
                     '_lots': order.quantity,
                     # '_SL': order.stop_loss,  # SL/TP in POINTS,
                     '_SL': 0,
                     # not pips.
                     # '_TP': order.take_profit,
                     '_TP': 0,
                     '_comment': comment,
                     '_magic': 123456,
                     '_type': actions[order.action]}

        # Reset thread data output
        self.client._set_response_(None)

        if order.type in ['market']:
            exec_dict['_price'] = 0
        elif order.type in ['limit']:
            exec_dict['_price'] = order.price

        if up_date:
            exec_dict['_action'] = 'MODIFY'
            exec_dict['_ticket'] = order.orederId
        else:
            exec_dict['_action'] = 'OPEN'
            exec_dict['_ticket'] = 0
            _check = '_action'
            self.client.MTX_NEW_TRADE_(_order=exec_dict)

        if _verbose:
            print('\n[{}] {} -> MetaTrader'.format(exec_dict['_comment'],
                                                   str(exec_dict)))

        return self.get_return(_check=_check)

    def send_order(self, order: dataclasses.dataclass):
        """
        Send Normal order or close trade
        Parameters
        ----------
        order: event order
        """

        if order.action_mt4 == 'normal':
            self.send_order_normal(order)

        elif order.action_mt4 == 'close_trade':
            # Close total
            logger.info(f'Sending Order to close positions in ticker: {order.ticker} quantity: {order.quantity}')
            self.client._set_response_(None)
            self.client.MTX_CLOSE_TRADE_BY_TICKET_(order.order_id_receiver)
            respond_order = self.get_return()

        # partially closed trade
        elif order.action_mt4 == 'close_partial':
            logger.info(f'Sending Order to close partial positions in ticker: {order.ticker} quantity: {order.quantity}')
            self.client._set_response_(None)
            self.client.MTX_CLOSE_PARTIAL_BY_TICKET_(
                order.order_id_receiver, order.quantity)
            respond_order = self.get_return()

        if order.action_mt4 != 'normal':
            try:
                # Saving order_id en order
                order.order_id_receiver = str(respond_order['_ticket'])
                if respond_order['_action'] == 'CLOSE':
                    logger.info(f'order closes successfully in ticker: {order.ticker} quantity: {order.quantity}'
                                f' with id: {order.order_id_receiver}')
                    order.status = 'closed'
                    order.filled_price = float(respond_order['_close_price'])
                    quantity_execute = respond_order['_close_lots']
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

    def close_all_positions(self):
        """
        Close all positions.
        """
        self.client.MTX_CLOSE_ALL_TRADES_()

    def get_trades_all_info(self, _delay=0.1, _wbreak=10):
        """ Fails when there are more than 16 open orders
           Returns the open trades with all the information
        """
        response = self.get_response('_trades')

        if response is None:
            logger.error('No response received, either there are no open trades or check the connection')
            print('No response received, either there are no open trades or check the connection')
            return None
        else:
            return response

    def get_stream_quotes_changes(self, tickers, callback=None):

        """
        :param tickers, list of ticker
        :param callback:
        :return:
        """

        self.client.MTX_SET_MARKETDATA_CALLBACK(callback)

        for _ti in tickers:
            self.client.MTX_SUBSCRIBE_MARKETDATA_(_symbol=_ti)

    def get_balance(self, _delay=0.1, _wbreak=10):
        """
        Get Balance
        """
        response = self.get_response('_info')

        if response is None:
            logger.error('No response received, either there are no open trades or check the connection')
            print('No response received, either there are no open trades or check the connection')
            return None
        else:
            return response

    def get_return(self,
                   _delay=0.250,
                   _wbreak=22,
                   _check='_action'):

        # While loop start time reference
        _ws = dt.datetime.utcnow()

        # While data not received, sleep until timeout
        while not self.client._valid_response_('zmq'):
            sleep(_delay)

            if (dt.datetime.utcnow() - _ws).total_seconds() > (
                    _delay * _wbreak):
                break

        # If data received, return response
        if self.client._valid_response_('zmq'):
            msg = self.client._get_response_()
            if _check in msg.keys():
                return msg
        # Default
        return None

    def check_order(self):
        """ Check open order and send changes to Portfolio  and for saving in the database"""
        current_positions = self.get_trades_all_info()
        if current_positions is None:
            current_positions = self.get_trades()
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
                self.emit_orders.publish_event('order_status', order)
            print(f'Order {order.status} {order}')

        for order_id in list_changing:
            # eliminate from dict_open_orders and create in dict_cancel_and_close_orders
            self.dict_open_orders.pop(order_id)
            self.dict_cancel_and_close_orders[order_id] = order


def get_realtime_data(settings: dict = {'symbols': List[str]}, callback: callable = _callable) -> None:
    """Return realtime data for a list of symbols. [Source: MT4 Darwinex]

    Parameters
    ----------
    settings
    symbols: List[str]
        Symbols of the assets. Example: AUDNZD, EURUSD
    callback: callable (data: Dict) -> None

    """

    symbols = settings['symbols']
    trading = Trading(type_service='provider')
    trading.get_stream_quotes_changes(symbols, callback)
