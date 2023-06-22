import ib_insync
import pandas as pd
from typing import Dict
from src.domain.abstractions.abstract_trading import Abstract_Trading
from ib_insync import MarketOrder, LimitOrder
import datetime as dt
import time
from src.infrastructure.brokerMQ import Emit_Events
from src.application.base_logger import logger
from datetime import datetime, timedelta
from IPython import get_ipython


ipython = get_ipython()
if 'IPKernelApp' in ipython.config:  # 'ipykernel' is used by Jupyter notebook
    ib_insync.util.startLoop()  # only use in Jupyter

# default Callable
async def _callable(data: Dict) -> None:
    """Callback function for realtime data. [Source: Crypto Exchange]

    Parameters
    ----------
    data: Dict
        Realtime data.
    """
    print(data)


class Trading(Abstract_Trading):
    def __init__(self, send_orders_status: bool = True, exchange_or_broker='ib', config_broker: Dict = {}, config_brokermq: Dict = {},
                 path_ticker = ''):
        super().__init__(send_orders_status=send_orders_status, exchange_or_broker=exchange_or_broker,
                         config_broker=config_broker)
        self.contract_from_contractIB = {}
        self.ticker_info = pd.read_csv(path_ticker, encoding="utf-8", sep=",")
        self.sleep = None

        if self.send_orders_status:
            self.emit_orders = Emit_Events(config=config_brokermq)
        else:
            self.emit_orders = None
        self.dict_from_strategies = {}
        self.dict_open_orders = {}

    def get_client(self):
        """
           Conect to ib api
        """
        try:
            self.client = ib_insync.IB()
            if 'IPKernelApp' in ipython.config:
                self.client.connect('172.17.0.1', self.config_broker['PORT_IB'], self.config_broker['CLIENT_IB'])
            else:
                self.client.connect(self.config_broker['HOST_IB'], self.config_broker['PORT_IB'], self.config_broker['CLIENT_IB'])
            self.sleep = self.client.sleep
            print(self.client)
            return self.client
        except Exception as ex:
            self._open = False
            logger.error(
                f'Error Connecting ib, Exception: {ex}')
            print(ex)

    def close(self):
        """
           Disconnect

        """
        print('Closing conection with API')
        logger.info('Closing conection with API')
        self.client.disconnect()
        self._open = False

    def start_update_orders_status(self) -> None:
        """Start update orders status."""
        try:
            if len(self.dict_open_orders) > 0:  # if there are open orders
                self._check_order()
                time.sleep(30)
            else:
                time.sleep(1)
        except Exception as ex:
            logger.error(
                f'Error check_order Exception: {ex}')

    def get_contractIB_from_contract(self, contract):
        try:
            ticker = contract
            sel = self.ticker_info[self.ticker_info.ticker == ticker]
            if len(sel) == 0: # if the ticker is different from the contract
                ticker = contract[:-3]
                sel = self.ticker_info[self.ticker_info.ticker == ticker]
            type_contract = sel.type.values[0]  # We are looking for a type of contract

            if type_contract == 'FUT':
                _new = ib_insync.Future()
                ## add info
                _new.exchange = sel.exchange_ib.values[0].rstrip().strip()
                _new.secType = 'FUT'
                _new.multiplier = sel.multiplier.values[0]
                _new.currency = sel.currency.values[0].rstrip().strip()
                _new.symbol = sel.ticker_ib.values[0].rstrip().strip()
                mm, year = self.year_month_by_ticker(contract)
                _new.lastTradeDateOrContractMonth = str(int(year * 100 + mm))
            elif type_contract == 'FOREX':
                _new = ib_insync.Forex(contract)
                _new.exchange = 'IDEALPRO'
            elif type_contract == 'STOCK':
                _new = ib_insync.Stock()
                _new.symbol = sel.ticker_ib.values[0].rstrip().strip()
                _new.secType = "STK"
                _new.exchange = sel.exchange_ib.values[0].rstrip().strip()
                _new.primaryExchange = sel.primaryExchange.values[0].rstrip().strip()
                _new.currency = sel.currency.values[0].rstrip().strip()
            elif type_contract == 'CFD':
                _new = ib_insync.CFD()
                ## add info
                _new.exchange = sel.exchange_ib.values[0].rstrip().strip()
                _new.secType = 'CFD'
                _new.currency = sel.currency.values[0].rstrip().strip()
                _new.symbol = sel.ticker_ib.values[0].rstrip().strip()

            self.client.qualifyContracts(_new)
            self.contract_from_contractIB[_new] = contract
            return _new

        except Exception as ex:
            print(f'Error: {ex}')
            logger.error(
                f'Error Get contract ib, Exception: {ex}')

    def char_by_month(self, month):
        """Calculate month through letter used in contracts
           of futures, the letter has to be a string"""
        if month == 1:
            cmes = 'F'
        elif month == 2:
            cmes = 'G'
        elif month == 3:
            cmes = 'H'
        elif month == 4:
            cmes = 'J'
        elif month == 5:
            cmes = 'K'
        elif month == 6:
            cmes = 'M'
        elif month == 7:
            cmes = 'N'
        elif month == 8:
            cmes = 'Q'
        elif month == 9:
            cmes = 'U'
        elif month == 10:
            cmes = 'V'
        elif month == 11:
            cmes = 'X'
        elif month == 12:
            cmes = 'Z'
        else:
            cmes = '0'
        return cmes

    def month_by_char(self, month):
        """calula mes a traves de letra utilizada en los contratos
           de futuros, la letra tiene que ser un char"""
        if month == 'F':
            cmes = 1
        elif month == 'G':
            cmes = 2
        elif month == 'H':
            cmes = 3
        elif month == 'J':
            cmes = 4
        elif month == 'K':
            cmes = 5
        elif month == 'M':
            cmes = 6
        elif month == 'N':
            cmes = 7
        elif month == 'Q':
            cmes = 8
        elif month == 'U':
            cmes = 9
        elif month == 'V':
            cmes = 10
        elif month == 'X':
            cmes = 11
        elif month == 'Z':
            cmes = 12
        else:
            cmes = 0
        return int(cmes)

    def _descompose(self, c):
        """get expiration month and year in string"""
        i = -1
        for y in range(len(c)):
            try:
                int(c[i])
            except:
                return c[i], c[i + 1:]
            i -= 1

    def year_month_by_ticker(self, _ticker, last_trade_date=None):
        """calculates year and month of the ticker(contract)
           the ticker must be symbol + month + year
           lastTradeDate: last trading day of the contract"""
        try:
            ticker_split = _ticker.split(' ')
            if len(ticker_split) == 1:  # 'ADH2001' o 'ADH01
                ticker = ticker_split[0]
            elif len(ticker_split) == 2:  # 'A1G4 Curncy'
                ticker = ticker_split[0]
            else:  # '_c G4 Curncy'
                ticker = ticker_split[0] + ticker_split[1]

            month_str, year_str = self._descompose(ticker)
            month = self.month_by_char(month_str)
            year = None
            if len(year_str) == 1:  # bloomberg format for active contracts
                year = None
            elif len(year_str) == 2 and last_trade_date is None:  # ADH01
                year = 1900 + int(year_str)
                if year < 1970:
                    year += 100
                return int(month), int(year)
            elif len(year_str) == 4:  # ADH2001:
                year = int(year_str)
            mm = int(month)

            if last_trade_date is not None:
                if mm >= last_trade_date.month:
                    year = last_trade_date.year
                else:
                    year = last_trade_date.year + 1
        except:  # comes with symbol format +yyyy+mm
            _ticker = str(int(_ticker))
            year = int(_ticker[-6:-2])
            mm = int(_ticker[-2:])
        return mm, year

    def get_ticker_info(self, contract, real_time=True):
        self.set_real_time(real_time)
        contractIB = self.get_contractIB_from_contract(contract)
        ticker_info = self.client.reqMktData(contractIB, '', False, False)
        self.client.sleep(0.1)
        return ticker_info

    def is_connected(self):
        return self.client.isConnected()

    def set_real_time(self, real_time):
        if real_time:
            self.client.reqMarketDataType(1)
        else:
            self.client.reqMarketDataType(3)

    def get_stream_quotes_changes(self, tickers, callback=None, real_time=True):
        """
             :param tickers, list of ticker
             :param callback:
             :param real_time:
             """
        self.set_real_time(real_time)

        for _c in tickers:
            contractIB = self.get_contractIB_from_contract(_c)  # create ticker IB
            # Suscribirse a los precios de los contratos
            self.client.reqMarketDataType(4)  # 4 = instantánea
            self.client.reqMktData(contractIB, '', False, False, None)
            print('Streaming : ' + str(contractIB))
        # Asignar la función de callback a los tickers
        self.client.pendingTickersEvent += callback
        # Esperar hasta que se reciban los precios
        self.client.run()

    def get_historical_data(self, symbols=None, timeframe=1, unit='Daily', start_date=dt.datetime(2017, 1, 1),
                                end_date=dt.datetime.today()):
        """
        Get historical data for a given symbol(s) from Interactive Brokers

        :param symbols: str or list of str; the symbol(s) to retrieve historical data for
        :param timeframe: int; the timeframe for each data point, in minutes (e.g. 1 for 1 minute bars)
        :param unit: str; the unit of the data (e.g. 'Daily' for daily bars, 'Hour' for hourly bars, 'Min' for minute bars)
        :param start_date: datetime; the start date for the data range
        :param end_date: datetime; the end date for the data range
        :return: pd.DataFrame containing the historical data for the specified symbol(s)
        """

        ## Create contrat IB
        # Convert symbol(s) to IB contract object
        contractIB = self.get_contractIB_from_contract(symbols)

        # Create empty DataFrame to store the historical data
        df = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])

        # Split the date range into 10-day intervals
        interval_length = timedelta(days=10)
        intervals = [(start_date + i * interval_length, min(start_date + (i + 1) * interval_length, end_date)) for i
                     in
                     range((end_date - start_date) // interval_length + 1)]

        # Convert timeframe to an integer
        timeframe = int(timeframe)

        # Iterate through the date ranges and request the historical data for each interval
        for start, end in intervals:
            # Convert end date to string in the format required by IB API
            print(start)
            end_str = end.strftime("%Y%m%d %H:%M:%S")
            duration = start - end
            days = str(abs(duration.days))
            if days == '0':  # filter
                days = '1'
            durationStr = days + ' D'
            whatToShow = 'TRADES'
            if contractIB.exchange == 'IDEALPRO':
                whatToShow = 'MIDPOINT'

            # Determine the bar size based on the timeframe and unit parameters
            if unit.lower() in ['daily', 'day']:
                _unit = 'day'
            elif unit.lower() == 'hour':
                _unit = 'hour'
            elif unit.lower() in ['minute', 'min']:
                _unit = 'min'
                if timeframe > 1:
                    _unit = 'mins'
            barSizeSetting = str(timeframe) + ' ' + _unit

            # Request the historical data from IB API
            bars = self.client.reqHistoricalData(contractIB, endDateTime=end_str, durationStr=durationStr,
                                                 barSizeSetting=barSizeSetting,
                                                 whatToShow=whatToShow,
                                                 useRTH=0,
                                                 formatDate=2)

            # Convert the returned bars to a pandas DataFrame and append it to the main DataFrame
            bars_df = ib_insync.util.df(bars)
            df = df.append(bars_df, ignore_index=True)

            # Create a new column with datetime objects for easier indexing and plotting
            _dtime = []
            for i in range(len(df['date'])):
                d = df['date'].loc[i]
                if _unit == 'day':
                    _dtime.append(dt.datetime(d.year, d.month, d.day))
                else:
                    _dtime.append(dt.datetime(d.year, d.month, d.day, d.hour, d.minute))

            df['datetime'] = _dtime
            df.index = _dtime

        df['ticker'] = symbols
        df['symbol'] = symbols
        df['multiplier'] = 1
        df['exchange'] = 'ib'
        df['dtime_zone'] = 'utc'
        df['provider'] = 'ib'
        df['freq'] = _unit
        df = df.drop(columns=['date'])

        return df

    def get_account_positions(self, account_keys):
        """
         Account positions
        :param _account_keys:
        :return:
        """
        if type(account_keys) is not list:  # check if it is a list
            _account_keys = [account_keys]
        positions_total = {}
        try:
            for account_id in _account_keys:
                positions = self.client.positions(account_id)
                self.client.sleep(0.2)
                positions_total[account_id] = {}
                for pos in positions:
                    # seach symbol
                    info_contract = pos.contract.dict()
                    info_contract_month = info_contract['lastTradeDateOrContractMonth']
                    if info_contract_month != '':
                        _symbol = info_contract['symbol']
                        local_symbol = info_contract['localSymbol']
                        symbol = f'{_symbol}{local_symbol[-2:-1]}{info_contract_month[2:-4]}'
                    else:
                        sec_type = info_contract['secType']
                        if sec_type == 'CASH':
                            local_symbol = info_contract['localSymbol']
                            symbol = local_symbol.replace('.', '')
                        else:
                            symbol = info_contract['localSymbol']
                    positions_total[account_id][symbol] = pos.position

        except Exception as ex:
            logger.error(
                f'Error Get Account Positions ib, Exception: {ex}')
            print(ex)
        return positions_total

    def get_total_balance(self, account_keys):
        try:
            info_balance = {'value': None, 'currency': None, 'real_time_buyingpower': None,
                            'real_time_initial_margin': None, 'value_stock': None, 'currency_stock': None}
            balance = self.client.accountSummary(account_keys)
            self.client.sleep(0.2)
            for x in range(len(balance)):
                info_row = balance[x]
                tag = info_row.tag
                if tag == 'TotalCashValue':
                    info_balance['value'] = info_row.value
                    info_balance['currency'] = info_row.currency
                if tag == 'BuyingPower':
                    info_balance['real_time_buyingpower'] = info_row.value
                if tag == 'InitMarginReq':
                    info_balance['real_time_initial_margin'] = info_row.value
                if tag == 'NetLiquidation':
                    info_balance['value_stock'] = info_row.value
                    info_balance['currency_stock'] = info_row.currency
        except Exception as ex:
            logger.error(
                f'Error Get Balance ib, Exception: {ex}')
            print(ex)

        return info_balance

    def send_order(self, order, transmit=False):

        try:
            logger.info(f'Sending Order to IB in ticker: {order.ticker} quantity: {order.quantity}')
            self.dict_from_strategies[order.order_id_sender] = order  # save order in dict_from_strategies
            ## Create contrato IB
            contractIB = self.get_contractIB_from_contract(order.ticker)

            if order.type in ['market', 'mercado']:
                order_ib = MarketOrder(order.action, int(order.quantity))
                order_ib.account = order.account
            elif order.order_type in ['limit', 'limitada']:
                order_ib = LimitOrder(order.action, int(order.quantity), order.price)
                order_ib.account = order.account_id
                if order.duration == 'DAY':
                    order_ib.tif = 'Day'
                else:
                    order_ib.tif = order.duration
            # send order to exchange
            logger.info(f'Sending Order to ib in ticker: {order.ticker} quantity: {order.quantity}')
            order_ib.transmit = transmit
            trade = self.client.placeOrder(contractIB, order_ib)
            self.client.sleep(0.2)
            print(trade)
            ## saving order_id in order
            order.order_id_receiver = str(trade.order.orderId)
            order.trace_id = str(trade.order.permId)

            if trade.orderStatus.status in ['Submitted', 'PendingSubmit', 'PreSubmitted', 'Filled']:
                order.status = 'open'
                order.datetime_in = dt.datetime.utcnow()
            else:
                logger.error(
                    f'Error in order in ticker: {order.ticker} quantity: {order.quantity} with id: '
                    f'{order.order_id_receiver}')
                order.order_status = 'error'

            if order.status == "error":
                print(f'Error sending order {order}')
                if self.send_orders_status:  # publish order status with error
                    self.emit_orders.publish_event('order_status', order)
            else:
                # eliminate from dict_from_strategies and create it in dict_open_orders
                self.dict_from_strategies.pop(order.order_id_sender)
                self.dict_open_orders[order.order_id_sender] = order
            self.client.sleep(0.2)
        except Exception as ex:
            logger.error(
                f'Error sending order: {ex}')
            print(ex)


    def cancel_order(self, order_id):
        """
        :param order_id:
        :return:
        """
        self.client.cancelOrder(order_id)

    def get_info_order(self, order_id) -> None:
        """Get info orders.

        Parameters
        ----------
        order_id
        """
        try:
            trades = self.client.trades()
            self.client.sleep(0.2)
            trade_orden_id = next((t for t in trades if t.order.orderId == int(order_id)), None)
        except Exception as ex:
            print(ex)
        return trade_orden_id

    def _check_order(self):
        """ Check open order and send changes to Portfolio  and for saving in the database"""
        list_changing = []
        for order_id in self.dict_open_orders.keys():
            order = self.dict_open_orders[order_id]
            info_order = self.get_info_order(order.order_id_receiver)
            if info_order is not None:
                order_status = info_order.orderStatus
                remaining =  order_status.remaining
                status = order_status.status
                if remaining == 0 and status == 'Filled':
                    order.status = 'closed'
                    order.filled_price = order_status.avgFillPrice
                    order.quantity_execute = order_status.filled
                    order.quantity_left = order.quantity - order.quantity_execute
                if status == 'cancelled':
                    order.status = 'cancelled'
                    order.filled_price = order_status.avgFillPrice
                    order.quantity_execute = order_status.filled
                    order.quantity_left = order.quantity - order.quantity_execute
                if order.status == 'closed' or order.status == 'cancelled':
                    list_changing.append(order_id)
                if self.send_orders_status:  # publish order status
                    self.emit_orders.publish_event('order_status', order)
                print(f'Order {order.status} {order}')

        for order_id in list_changing:
            # eliminate from dict_open_orders and create in dict_cancel_and_close_orders
            self.dict_open_orders.pop(order_id)
            self.dict_cancel_and_close_orders[order_id] = order


