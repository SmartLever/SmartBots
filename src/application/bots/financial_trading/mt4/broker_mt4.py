""" Recieved events orders from Portfolio and send it to the broker or exchange for execution"""
from src.infraestructure.brokerMQ import Emit_Events
from src.domain.events import Positions
import pytz
from src.domain.base_logger import logger
from typing import Dict
from src.application import conf
import datetime as dt
from src.infraestructure.mt4.mt4_model import Trading
from src.infraestructure.health_handler import Health_Handler
from src.infraestructure.database_handler import Universe
from src.domain import events


class BrokerMT4(object):
    """
    Class
    for broker MT4.

    """

    def __init__(self, config_brokermq: Dict = {}, send_orders_status=True, exchange_or_broker='darwinex'):
        self.config_brokermq = config_brokermq
        self.config_broker = {'MT4_HOST': conf.MT4_HOST, 'CLIENT_IF': conf.CLIENT_IF, 'PUSH_PORT': conf.PUSH_PORT,
                              'PULL_PORT_BROKER': conf.PULL_PORT_BROKER, 'SUB_PORT_BROKER': conf.SUB_PORT_BROKER}
        self.trading = Trading(send_orders_status=send_orders_status, exchange_or_broker=f'{exchange_or_broker}_broker',
                               config_broker=self.config_broker, config_brokermq=self.config_brokermq)
        # Log event health of the service
        self.health_handler = Health_Handler(n_check=6,
                                             name_service='broker_mt4',
                                             config=self.config_brokermq)
        self.emit = Emit_Events(config=config_brokermq)
        self.name_portfolio = conf.NAME_FINANCIAL_PORTOFOLIO
        # Create library for saving balances
        name = 'balance'
        # Create connection  to DataBase
        store = Universe(host=conf.MONGO_HOST, port=conf.MONGO_PORT)
        self.lib_balance = store.get_library(name, library_chunk_store=False)
        # Launch thead for update orders status
        self.trading.start_update_orders_status()

    def check_balance(self) -> None:
        try:
            balance = self.trading.get_total_balance()
            if balance is not None:
                now = dt.datetime.utcnow()
                print(f'Balance {balance} {dt.datetime.utcnow()}')
                # Control Balance
                control_balance = dt.datetime(now.year, now.month, now.day, 20, 0, 0)
                unique = f'{self.name_portfolio}_{control_balance.strftime("%Y-%m-%d %H:00:00")}'
                # if time is lower control balance, compare with yesterday balance
                if now < control_balance:
                    control_balance = control_balance - dt.timedelta(days=1)
                    unique = f'{self.name_portfolio}_{control_balance.strftime("%Y-%m-%d %H:00:00")}'
                # if time is greater 20 utc and weekday is monday to friday
                if now >= control_balance and now.weekday() in [0, 1, 2, 3, 4]:
                    # check if the symbols is saving
                    if self.lib_balance.has_symbol(unique) is False:
                        # saving objective balance
                        balance = events.Balance(datetime=now, balance=balance,
                                                 account=self.name_portfolio)

                        self.lib_balance.write(unique, balance, metadata={'datetime': now,
                                                                     'account': self.name_portfolio})
                # if this portfolio has a close positions
                if self.lib_balance.has_symbol(unique) and conf.PERCENTAGE_CLOSE_POSITIONS_MT4 is not None:
                    # compare current balance and objective balance
                    data = self.lib_balance.read(unique).data
                    try:
                        diff_perce = (balance - data.balance) / data.balance * 100
                        print(f'Current diff {diff_perce}')
                        # if current return is lower than objective, send close positions
                        if diff_perce <= float(conf.PERCENTAGE_CLOSE_POSITIONS_MT4):
                            # send to close all positions
                            function_to_run = 'close_all_positions'  # get_saved_values_strategy
                            petition_pos = events.Petition(datetime=now, function_to_run=function_to_run,
                                                           name_portfolio=self.name_portfolio)

                            print(f'Send close all positions: Percetage Diff {diff_perce}')
                            self.emit.publish_event('petition', petition_pos)

                    except Exception as e:
                        logger.error(f'Error closing positions in MT4 broker: {e}')
                self.health_handler.check()

            else:
                logger.error(f'Error Getting MT4 Balance')
                self.health_handler.send(description='Error Getting MT4 Balance', state=0)

        except Exception as e:
            logger.error(f'Error Getting MT4 Balance: {e}')
            self.health_handler.send(description=e, state=0)

    def save_positions(self) -> None:
        try:
            #  save MT4 positions
            positions = self.trading.get_account_positions()
            _d = dt.datetime.utcnow()
            dtime = dt.datetime(_d.year, _d.month, _d.day,
                                _d.hour, _d.minute, _d.second, 0, pytz.UTC)

            positions_event = Positions(ticker=f'real_positions_{conf.BROKER_FINANCIAL}',
                                        account=f'{conf.BROKER_FINANCIAL}_mt4_positions',
                                        positions=positions, datetime=dtime)
            self.emit.publish_event('positions', positions_event)

        except Exception as e:
            logger.error(f'Error Saving MT4 Positions: {e}')

    def send_broker(self, event) -> None:
        """Send order.

        Parameters
        ----------
        order: event order
        """
        if event.event_type == 'order' and conf.SEND_ORDERS_BROKER_MT4 == 1:
            event.exchange_or_broker = f'mt4_{conf.BROKER_FINANCIAL}'
            qtypes = {'buy': 1, 'sell': 0}  # the opposite position to the order
            symbol = event.ticker
            quantity = event.quantity
            open_trades = self.trading.get_trades()
            if open_trades is not None:
                trades_id = list(open_trades.keys())
                # Loop every trade
                for trade_id in trades_id:
                    trade = open_trades[trade_id]
                    # same symbol
                    if symbol == trade['_symbol']:
                        if trade['_type'] == qtypes[event.action]:
                            if quantity != 0:
                                if quantity > trade['_lots'] or quantity == trade['_lots']:
                                    # Close trade
                                    event.action_mt4 = 'close_trade'
                                    event.order_id_receiver = trade_id
                                    logger.info(
                                        f'Sending Order to close positions in ticker: {event.ticker} quantity: {event.quantity}')
                                    self.trading.send_order(event)
                                    quantity -= trade['_lots']
                                else:
                                    # Partially closed trade
                                    event.action_mt4 = 'close_partial'
                                    event.order_id_receiver = trade_id
                                    event.quantity = quantity
                                    logger.info(
                                        f'Sending Order to close partial positions in ticker: {event.ticker} quantity: {event.quantity}')
                                    self.trading.send_order(event)
                                    quantity = 0
                if quantity != 0:
                    # send a normal order
                    logger.info(f'Sending Order to MT4 in ticker: {event.ticker} quantity: {event.quantity}')
                    event.quantity = quantity
                    event.action_mt4 = 'normal'
                    self.trading.send_order(event)

        elif event.event_type == 'order' and conf.SEND_ORDERS_BROKER_MT4 == 0:
            event.exchange_or_broker = f'mt4_{conf.BROKER_FINANCIAL}'
            print(f'Order for {event.ticker} recieved but not send.')

