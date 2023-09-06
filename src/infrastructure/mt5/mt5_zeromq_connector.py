from datetime import datetime
from pytz import timezone
from tzlocal import get_localzone
from queue import Queue
from threading import Thread
import time
import zmq
import pandas as pd

class Functions:
    def __init__(self, host=None, debug=None, type_service='broker'):
        self.debug = debug or True
        self.HOST = host or 'localhost'
        if type_service == 'provider':
            self.live_socket_instance = None
            self.LIVE_PORT = 15557  # PUSH/PULL port
        else:
            self.SYS_PORT = 15555  # REP/REQ port
            self.DATA_PORT = 15556  # PUSH/PULL port
            self.EVENTS_PORT = 15558  # PUSH/PULL port

            # ZeroMQ timeout in seconds
            sys_timeout = 100
            data_timeout = 1000

            # initialise ZMQ context
            context = zmq.Context()
            # connect to server sockets
            try:
                if type_service != 'provider':
                    self.sys_socket = context.socket(zmq.REQ)
                    # set port timeout
                    self.sys_socket.RCVTIMEO = sys_timeout * 1000
                    self.sys_socket.connect(
                        'tcp://{}:{}'.format(self.HOST, self.SYS_PORT))
                    #
                    self.data_socket = context.socket(zmq.PULL)
                    # set port timeout
                    self.data_socket.RCVTIMEO = data_timeout * 1000
                    self.data_socket.connect(
                        'tcp://{}:{}'.format(self.HOST, self.DATA_PORT))

            except zmq.ZMQError:
                raise zmq.ZMQBindError("Binding ports ERROR")

            except KeyboardInterrupt:
                self.sys_socket.close()
                self.sys_socket.term()
                self.data_socket.close()
                self.data_socket.term()


    def live_socket(self):
        """Connect to socket in a ZMQ context"""
        if not self.live_socket_instance:
            try:
                context = zmq.Context.instance()
                socket = context.socket(zmq.PULL)
                socket.connect('tcp://{}:{}'.format(self.HOST, self.LIVE_PORT))
                self.live_socket_instance = socket
            except zmq.ZMQError:
                raise zmq.ZMQBindError("Live port connection ERROR")
        return self.live_socket_instance

    def _send_request(self, data: dict) -> None:
        """Send request to server via ZeroMQ System socket"""
        try:
            self.sys_socket.send_json(data)
            msg = self.sys_socket.recv_string()
            # terminal received the request
            assert msg == 'OK', 'Something wrong on server side'
        except AssertionError as err:
            raise zmq.NotDone(err)
        except zmq.ZMQError:
            raise zmq.NotDone("Sending request ERROR")

    def _pull_reply(self):
        """Get reply from server via Data socket with timeout"""
        try:
            msg = self.data_socket.recv_json()
        except zmq.ZMQError:
            raise zmq.NotDone('Data socket timeout ERROR')
        return msg

    def Command(self, **kwargs) -> dict:
        """Construct a request dictionary from default and send it to server"""

        # default dictionary
        request = {
            "action": None,
            "actionType": None,
            "symbol": None,
            "chartTF": None,
            "fromDate": None,
            "toDate": None,
            "id": None,
            "ticket": None,
            "magic": None,
            "volume": None,
            "price": None,
            "stoploss": None,
            "takeprofit": None,
            "expiration": None,
            "deviation": None,
            "comment": None,
            "chartId": None,
            "indicatorChartId": None,
            "chartIndicatorSubWindow": None,
            "style": None,
        }

        # update dict values if exist
        for key, value in kwargs.items():
            if key in request:
                request[key] = value
            else:
                raise KeyError('Unknown key in **kwargs ERROR')

        # send dict to server
        self._send_request(request)

        # return server reply
        return self._pull_reply()

class Metatrader:

    def __init__(self, host=None, real_volume=None, tz_local=None, type_service='broker'):
        self.__api = Functions(host, type_service=type_service)
        if type_service != 'provider':
            self.real_volume = real_volume or False
            self.__tz_local = tz_local
            self.__utc_timezone = timezone('UTC')
            self.__my_timezone = get_localzone()
            self.__utc_brocker_offset = self.___utc_brocker_offset()


    def balance(self):
        return self.__api.Command(action="BALANCE")

    def accountInfo(self):
        return self.__api.Command(action="ACCOUNT")

    def positions(self):
        return self.__api.Command(action="POSITIONS")

    def orders(self):
        return self.__api.Command(action="ORDERS")

    def trade(self, symbol, actionType, volume, stoploss, takeprofit, price, deviation):
        return self.__api.Command(
            action="TRADE",
            actionType=actionType,
            symbol=symbol,
            volume=volume,
            stoploss=stoploss,
            takeprofit=takeprofit,
            price=price,
            deviation=deviation
        )

    def buy(self, symbol, volume, stoploss, takeprofit, deviation=5):
        price = 0
        return self.trade(symbol, "ORDER_TYPE_BUY", volume,
                   stoploss, takeprofit, price, deviation)

    def sell(self, symbol, volume, stoploss, takeprofit, deviation=5):
        price = 0
        return self.trade(symbol, "ORDER_TYPE_SELL", volume,
                   stoploss, takeprofit, price, deviation)

    def buyLimit(self, symbol, volume, stoploss, takeprofit, price=0, deviation=5):
        return self.trade(symbol, "ORDER_TYPE_BUY_LIMIT", volume,
                   stoploss, takeprofit, price, deviation)

    def sellLimit(self, symbol, volume, stoploss, takeprofit, price=0, deviation=5):
        return self.trade(symbol, "ORDER_TYPE_SELL_LIMIT", volume,
                   stoploss, takeprofit, price, deviation)

    def buyStop(self, symbol, volume, stoploss, takeprofit, price=0, deviation=5):
        return self.trade(symbol, "ORDER_TYPE_BUY_STOP", volume,
                   stoploss, takeprofit, price, deviation)

    def sellStop(self, symbol, volume, stoploss, takeprofit, price=0, deviation=5):
        return self.trade(symbol, "ORDER_TYPE_SELL_LIMIT", volume,
                   stoploss, takeprofit, price, deviation)

    def cancel_all(self):
        orders = self.orders()

        if 'orders' in orders:
            for order in orders['orders']:
                self.CancelById(order['id'])

    def close_all(self):
        positions = self.positions()

        if 'positions' in positions:
            for position in positions['positions']:
                self.CloseById(position['id'])

    def positionModify(self, id, stoploss, takeprofit):
        return self.__api.Command(
            action="TRADE",
            actionType="POSITION_MODIFY",
            id=id,
            stoploss=stoploss,
            takeprofit=takeprofit
        )

    def ClosePartial(self, id, volume):
        return self.__api.Command(
            action="TRADE",
            actionType="POSITION_PARTIAL",
            id=id,
            volume=volume
        )

    def CloseById(self, id):
        return self.__api.Command(
            action="TRADE",
            actionType="POSITION_CLOSE_ID",
            id=id
        )

    def CloseBySymbol(self, symbol):
        return self.__api.Command(
            action="TRADE",
            actionType="POSITION_CLOSE_SYMBOL",
            symbol=symbol,
        )

    def orderModify(self, id, stoploss, takeprofit, price):
        return self.__api.Command(
            action="TRADE",
            actionType="ORDER_MODIFY",
            id=id,
            stoploss=stoploss,
            takeprofit=takeprofit,
            price=price
        )

    def CancelById(self, id):
        return self.__api.Command(
            action="TRADE",
            actionType="ORDER_CANCEL",
            id=id
        )

    def ___utc_brocker_offset(self):
        utc = datetime.now(self.__utc_timezone).strftime('%Y-%m-%d %H:%M:%S')
        try:
            broker = self.accountInfo()
            broker = datetime.strptime(broker['time'], '%Y.%m.%d %H:%M:%S')
        except KeyError:
            raise "Metatrader 5 Server is disconnect"
        utc = datetime.strptime(utc, '%Y-%m-%d %H:%M:%S')

        duration = broker - utc
        duration_in_s = duration.total_seconds()
        hour = divmod(duration_in_s, 60)[0]
        seconds = int(hour) * 60
        return seconds

    def _price(self, callback):
        connect = self.__api.live_socket()
        while True:
            price = connect.recv_json()
            try:
                data_price = price['data']
                df_price = pd.DataFrame([data_price])
                df_price = df_price.set_index([0])
                df_price.index.name = 'date'
                if self._allchartTF == 'TICK':
                    if price['symbol'] in self._allsymbol_:
                        callback(price)
                elif self._allchartTF == 'TS':
                    df_price.index = pd.to_datetime(df_price.index, unit='ms')
                    df_price.columns = ['type', 'bid', 'ask', 'last', 'volume']
                    callback(df_price)
                else:
                    if self.real_volume:
                        del df_price[5]
                    else:
                        del df_price[6]
                    df_price.index = pd.to_datetime(df_price.index, unit='s')
                    df_price.columns = ['open', 'high', 'low', 'close', 'volume', 'spread']
                    callback(df_price)


            except KeyError:
                pass

    def _start_thread_price(self, callback):
        t = Thread(target=self._price, args=(callback,), daemon=True)
        t.start()

    def price(self, symbol, chartTF, callback):
        self._allsymbol_ = symbol
        self._allchartTF = chartTF
        self._start_thread_price(callback)

