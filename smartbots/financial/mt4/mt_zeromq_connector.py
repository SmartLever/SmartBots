import zmq
from time import sleep
from datetime import datetime
from threading import Thread

class MTZeroMQConnector():
    """
    Setup ZeroMQ -> MetaTrader Connector
    """

    def __init__(self,
                 client_id='DLabs_Python',  # Unique ID for this client
                 host='localhost',  # Host to connect to
                 protocol='tcp',  # Connection protocol
                 push_port=32768,  # Port for Sending commands
                 pull_port=32769,  # Port for Receiving responses
                 sub_port=32770,  # Port for Subscribing for prices
                 delimiter=';',
                 market_data_callback=None,  # Callback for Market data_crypto
                 verbose=False):  # String delimiter

        # Strategy Status (if this is False, ZeroMQ will not listen for data_crypto)
        self._ACTIVE = True

        # Client ID
        self._ClientID = client_id

        # ZeroMQ Host
        self._host = host

        # Connection Protocol
        self._protocol = protocol

        # Market data_crypto callback
        self._market_data_callback = market_data_callback

        # ZeroMQ Context
        self._ZMQ_CONTEXT = zmq.Context()

        # TCP Connection URL Template
        self._URL = self._protocol + "://" + self._host + ":"

        # Ports for PUSH, PULL and SUB sockets respectively
        self._PUSH_PORT = push_port
        self._PULL_PORT = pull_port
        self._SUB_PORT = sub_port

        # Create Sockets
        self._PUSH_SOCKET = self._ZMQ_CONTEXT.socket(zmq.PUSH)
        self._PUSH_SOCKET.setsockopt(zmq.SNDHWM, 1)

        self._PULL_SOCKET = self._ZMQ_CONTEXT.socket(zmq.PULL)
        self._PULL_SOCKET.setsockopt(zmq.RCVHWM, 1)

        self._SUB_SOCKET = self._ZMQ_CONTEXT.socket(zmq.SUB)

        # Bind PUSH Socket to send commands to MetaTrader
        self._PUSH_SOCKET.connect(self._URL + str(self._PUSH_PORT))
        print("[INIT] Ready to send commands to METATRADER (PUSH): " + str(self._PUSH_PORT))

        # Connect PULL Socket to receive command responses from MetaTrader
        self._PULL_SOCKET.connect(self._URL + str(self._PULL_PORT))
        print("[INIT] Listening for responses from METATRADER (PULL): " + str(self._PULL_PORT))

        # Connect SUB Socket to receive market data_crypto from MetaTrader
        self._SUB_SOCKET.connect(self._URL + str(self._SUB_PORT))

        # Initialize POLL set and register PULL and SUB sockets
        self._poller = zmq.Poller()
        self._poller.register(self._PULL_SOCKET, zmq.POLLIN)
        self._poller.register(self._SUB_SOCKET, zmq.POLLIN)

        # Start listening for responses to commands and new market data_crypto
        self._string_delimiter = delimiter

        # BID/ASK Market Data Subscription Threads ({SYMBOL: Thread})
        self._MarketData_Thread = None

        # Begin polling for PULL / SUB data_crypto

        self._MarketData_Thread = Thread(target=self._MT_ZMQ_Poll_Data,
                                         args=(self._string_delimiter,
                                               self._market_data_callback))
        self._MarketData_Thread.start()

        # Market Data Dictionary by Symbol (holds tick data_crypto)
        self._Market_Data_DB = {}  # {SYMBOL: {TIMESTAMP: (BID, ASK)}}

        # Temporary Order STRUCT for convenience wrappers later.
        self.temp_order_dict = self._generate_default_order_dict()

        # Thread returns the most recently received DATA block here
        self._thread_data_output = None

        # Verbosity
        self._verbose = verbose

    ##########################################################################

    """
    Set Status (to enable/disable strategy manually)
    """

    def _setStatus(self, _new_status=False):

        self._ACTIVE = _new_status
        print("\n**\n[KERNEL] Setting Status to {} - Deactivating Threads.. please wait a bit.\n**".format(_new_status))

    ##########################################################################

    """
    Function to send commands to MetaTrader (PUSH)
    """

    def remote_send(self, _socket, _data):

        try:
            _socket.send_string(_data, zmq.DONTWAIT)
        except zmq.error.Again:
            print("\nResource timeout.. please try again.")
            sleep(0.000000001)

    ##########################################################################

    def _get_response_(self):
        return self._thread_data_output

    ##########################################################################

    def _set_response_(self, _resp=None):
        self._thread_data_output = _resp

    ##########################################################################

    def _valid_response_(self, _input='zmq'):

        # Valid data_crypto types
        _types = (dict)

        # If _input = 'zmq', assume self._zmq._thread_data_output
        if isinstance(_input, str) and _input == 'zmq':
            return isinstance(self._get_response_(), _types)
        else:
            return isinstance(_input, _types)

        # Default
        return False

    ##########################################################################

    """
    Function to retrieve data_crypto from MetaTrader (PULL or SUB)
    """

    def remote_recv(self, _socket):

        try:
            msg = _socket.recv_string(zmq.DONTWAIT)
            return msg
        except zmq.error.Again:
            print("\nResource timeout.. please try again.")
            sleep(0.000001)

        return None

    ##########################################################################

    # Convenience functions to permit easy trading via underlying functions.

    # OPEN ORDER
    def MTX_NEW_TRADE_(self, _order=None):

        if _order is None:
            _order = self._generate_default_order_dict()

        # Execute
        self.MTX_SEND_COMMAND_(**_order)

    # MODIFY ORDER
    def MTX_MODIFY_TRADE_BY_TICKET_(self, _ticket, _SL, _TP):  # in points

        try:
            self.temp_order_dict['_action'] = 'MODIFY'
            self.temp_order_dict['_SL'] = _SL
            self.temp_order_dict['_TP'] = _TP
            self.temp_order_dict['_ticket'] = _ticket

            # Execute
            self.MTX_SEND_COMMAND_(**self.temp_order_dict)

        except KeyError:
            print("[ERROR] Order Ticket {} not found!".format(_ticket))

    # CLOSE ORDER
    def MTX_CLOSE_TRADE_BY_TICKET_(self, _ticket):

        try:
            self.temp_order_dict['_action'] = 'CLOSE'
            self.temp_order_dict['_ticket'] = _ticket

            # Execute
            self.MTX_SEND_COMMAND_(**self.temp_order_dict)

        except KeyError:
            print("[ERROR] Order Ticket {} not found!".format(_ticket))

    # CLOSE PARTIAL
    def MTX_CLOSE_PARTIAL_BY_TICKET_(self, _ticket, _lots):

        try:
            self.temp_order_dict['_action'] = 'CLOSE_PARTIAL'
            self.temp_order_dict['_ticket'] = _ticket
            self.temp_order_dict['_lots'] = _lots

            # Execute
            self.MTX_SEND_COMMAND_(**self.temp_order_dict)

        except KeyError:
            print("[ERROR] Order Ticket {} not found!".format(_ticket))

    # CLOSE MAGIC
    def MTX_CLOSE_TRADES_BY_MAGIC_(self, _magic):

        try:
            self.temp_order_dict['_action'] = 'CLOSE_MAGIC'
            self.temp_order_dict['_magic'] = _magic

            # Execute
            self.MTX_SEND_COMMAND_(**self.temp_order_dict)

        except KeyError:
            pass

    # CLOSE ALL TRADES
    def MTX_CLOSE_ALL_TRADES_(self):

        try:
            self.temp_order_dict['_action'] = 'CLOSE_ALL'

            # Execute
            self.MTX_SEND_COMMAND_(**self.temp_order_dict)

        except KeyError:
            pass

    # GET OPEN TRADES
    def MTX_GET_ALL_OPEN_TRADES_(self):

        try:
            self.temp_order_dict['_action'] = 'GET_OPEN_TRADES'

            # Execute
            self.MTX_SEND_COMMAND_(**self.temp_order_dict)

        except KeyError:
            pass

    # GET OPEN POSITION
    def MTX_GET_POSITION_(self):

        try:
            self.temp_order_dict['_action'] = 'GET_POSITION'

            # Execute
            self.MTX_SEND_COMMAND_(**self.temp_order_dict)

        except KeyError:
            pass

    # GET BALANCE
    def MTX_GET_BALANCE_(self):

        try:
            self.temp_order_dict['_action'] = 'GET_BALANCE'

            # Execute
            self.MTX_SEND_COMMAND_(**self.temp_order_dict)

        except KeyError:
            pass

    # DEFAULT ORDER DICT
    def _generate_default_order_dict(self):
        return ({'_action': 'OPEN',
                 '_type': 0,
                 '_symbol': 'EURUSD',
                 '_price': 0.0,
                 '_SL': 500,  # SL/TP in POINTS, not pips.
                 '_TP': 500,
                 '_comment': 'DWX_Python_to_MT',
                 '_lots': 0.01,
                 '_magic': 123456,
                 '_ticket': 0})

    # DEFAULT DATA REQUEST DICT
    def _generate_default_data_dict(self):
        return ({'_action': 'DATA',
                 '_symbol': 'EURUSD',
                 '_timeframe': 1440,  # M1 = 1, M5 = 5, and so on..
                 '_start': '2018.12.21 17:00:00',  # timestamp in MT4 recognized format
                 '_end': '2018.12.21 17:05:00'})

    ##########################################################################
    """
    Function to construct messages for sending DATA commands to MetaTrader
    """

    def MTX_SEND_MARKETDATA_REQUEST_(self,
                                     _symbol='EURUSD',
                                     _timeframe=1,
                                     _start='2019.01.04 17:00:00',
                                     _end=datetime.now().strftime('%Y.%m.%d %H:%M:00')):
        # _end='2019.01.04 17:05:00'):

        _msg = "{};{};{};{};{}".format('DATA',
                                       _symbol,
                                       _timeframe,
                                       _start,
                                       _end)
        # Send via PUSH Socket
        self.remote_send(self._PUSH_SOCKET, _msg)

    ##########################################################################
    """
    Function to construct messages for sending Trade commands to MetaTrader
    """

    def MTX_SEND_COMMAND_(self, _action='OPEN', _type=0,
                          _symbol='EURUSD', _price=0.0,
                          _SL=50, _TP=50, _comment="Python-to-MT",
                          _lots=0.01, _magic=123456, _ticket=0):

        _msg = "{};{};{};{};{};{};{};{};{};{};{}".format('TRADE', _action, _type,
                                                         _symbol, _price,
                                                         _SL, _TP, _comment,
                                                         _lots, _magic,
                                                         _ticket)

        # Send via PUSH Socket
        self.remote_send(self._PUSH_SOCKET, _msg)

        """
         compArray[0] = TRADE or DATA
         compArray[1] = ACTION (e.g. OPEN, MODIFY, CLOSE)
         compArray[2] = TYPE (e.g. OP_BUY, OP_SELL, etc - only used when ACTION=OPEN)

         For compArray[0] == DATA, format is: 
             DATA|SYMBOL|TIMEFRAME|START_DATETIME|END_DATETIME

         // ORDER TYPES: 
         // https://docs.mql4.com/constants/tradingconstants/orderproperties

         // OP_BUY = 0
         // OP_SELL = 1
         // OP_BUYLIMIT = 2
         // OP_SELLLIMIT = 3
         // OP_BUYSTOP = 4
         // OP_SELLSTOP = 5

         compArray[3] = Symbol (e.g. EURUSD, etc.)
         compArray[4] = Open/Close Price (ignored if ACTION = MODIFY)
         compArray[5] = SL
         compArray[6] = TP
         compArray[7] = Trade Comment
         compArray[8] = Lots
         compArray[9] = Magic Number
         compArray[10] = Ticket Number (MODIFY/CLOSE)
         """
        # pass

    ##########################################################################

    """
    Function to check Poller for new reponses (PULL) and market data_crypto (SUB)
    """

    def _MT_ZMQ_Poll_Data(self,
                          string_delimiter=';',
                          # market_data_callback=None,
                          dictionary_DB=True):

        while self._ACTIVE:

            sockets = dict(self._poller.poll())

            # Process response to commands sent to MetaTrader
            if self._PULL_SOCKET in sockets and sockets[
                self._PULL_SOCKET] == zmq.POLLIN:

                try:

                    msg = self._PULL_SOCKET.recv_string(zmq.DONTWAIT)

                    # If data_crypto is returned, store as pandas Series
                    if msg != '' and msg != None:

                        try:
                            _data = eval(msg)

                            self._thread_data_output = _data
                            if self._verbose:
                                print(_data)  # default logic

                        except Exception as ex:
                            _exstr = "Exception Type {0}. Args:\n{1!r}"
                            _msg = _exstr.format(type(ex).__name__, ex.args)
                            print(_msg)

                except zmq.error.Again:
                    pass  # resource temporarily unavailable, nothing to print
                except ValueError:
                    pass  # No data_crypto returned, passing iteration.
                except UnboundLocalError:
                    pass  # _symbol may sometimes get referenced before being assigned.

            # Receive new market data_crypto from MetaTrader
            if self._SUB_SOCKET in sockets and sockets[
                self._SUB_SOCKET] == zmq.POLLIN:

                try:
                    msg = self._SUB_SOCKET.recv_string(zmq.DONTWAIT)

                    if msg != "":
                        _symbol, _data = msg.split(" ")
                        _bid, _ask = _data.split(string_delimiter)
                        _timestamp = str(datetime.utcnow())

                        if self._verbose:
                            print(
                                "\n[" + _symbol + "] " + _timestamp + " (" + _bid + "/" + _ask + ") BID/ASK")

                        # Update Market Data
                        if dictionary_DB:
                            if _symbol not in self._Market_Data_DB.keys():
                                self._Market_Data_DB[_symbol] = {}

                            self._Market_Data_DB[_symbol][_timestamp] = (
                                float(_bid), float(_ask))

                        if self._market_data_callback:
                            _event = {'Symbol': _symbol,
                                      'Time': _timestamp,
                                      'Bid': _bid,
                                      'Ask': _ask}
                            self._market_data_callback(_event)

                except zmq.error.Again:
                    pass  # resource temporarily unavailable, nothing to print
                except ValueError:
                    pass  # No data_crypto returned, passing iteration.
                except UnboundLocalError:
                    pass  # _symbol may sometimes get referenced before being assigned.

    ##########################################################################

    """
    Function to subscribe to given Symbol's BID/ASK feed from MetaTrader
    """

    def MTX_SUBSCRIBE_MARKETDATA_(self, _symbol, _string_delimiter=';'):

        # Subscribe to SYMBOL first.
        self._SUB_SOCKET.setsockopt_string(zmq.SUBSCRIBE, _symbol)

        if self._MarketData_Thread is None:
            self._MarketData_Thread = Thread(target=self._MT_ZMQ_Poll_Data,
                                             args=(_string_delimiter))
            self._MarketData_Thread.start()

        print(f"[KERNEL] Suscrito al {_symbol} para actualizaciones de BID/ASK ")
        # "self._Market_Data_DB.".format(_symbol))

    """
    Function to unsubscribe to given Symbol's BID/ASK feed from MetaTrader
    """

    def MTX_UNSUBSCRIBE_MARKETDATA_(self, _symbol):

        self._SUB_SOCKET.setsockopt_string(zmq.UNSUBSCRIBE, _symbol)
        print("\n**\n[KERNEL] Unsubscribing from " + _symbol + "\n**\n")

    def MTX_SET_MARKETDATA_CALLBACK(self, market_data_callback):
        self._market_data_callback = market_data_callback

    """
    Function to unsubscribe from ALL MetaTrader Symbols
    """

    def MTX_UNSUBSCRIBE_ALL_MARKETDATA_REQUESTS_(self):

        self._setStatus(False)
        self._MarketData_Thread = None

##########################################################################
