""" Telegram bot"""

from telegram.ext import Updater, CommandHandler
from functools import wraps
import threading
import datetime as dt
import time
from src.application import conf
from telegram import ReplyKeyboardMarkup, ParseMode
from telegram.error import NetworkError, TelegramError
import schedule
from src.infrastructure.database_handler import Universe
from src.infrastructure.brokerMQ import Emit_Events
from src.domain import events
from tabulate import tabulate
from src.domain.base_logger import logger
import os

if 'TRADING_TYPE_DOCKER' in os.environ:
    trading_type = os.environ['TRADING_TYPE_DOCKER']
else:
    trading_type = conf.TRADING_TYPE_TELEGRAM

if trading_type == 'crypto':
    from src.infraestructure.crypto.exchange_model import Trading
elif trading_type == 'betting':
    from src.infraestructure.api_berfair.betfair_model import Trading

reply_keyboard = [['/start']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)


# functions telegram
def restricted(func):
    """ Restriction function for ids"""

    @wraps(func)
    def wrapped(update, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            print("Unauthorized access denied for {}.".format(user_id))
            logger.info("Unauthorized access denied for {}.".format(user_id))
            update.message.reply_text('You are not authorized, please talk to the administrator, id ' + str(user_id))
            return
        return func(update, *args, **kwargs)

    return wrapped


def _send_msg(chat_id: str, msg: str, parse_mode: str = None,
              disable_notification: bool = False) -> None:
    """
    Send given markdown message
    :param chat_id: chat_id
    :param msg: message
    :param parse_mode: telegram parse mode
    :return: None
    """

    try:
        try:
            updater.bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=parse_mode,
                reply_markup=markup,
                disable_notification=disable_notification,
            )
        except NetworkError as network_err:
            # Sometimes the telegram server resets the current connection,
            # if this is the case we send the message again.
            print(
                'Telegram NetworkError: %s! Trying one more time.',
                network_err.message
            )
            logger.error(f'Telegram NetworkError: {network_err.message}')
            updater.bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=parse_mode,
                reply_markup=markup,
                disable_notification=disable_notification,
            )
    except TelegramError as telegram_err:
        print(
            'TelegramError: %s! Giving up on that message.',
            telegram_err.message
        )
        logger.error(f'TelegramError: {telegram_err.message}')

@restricted
def start(update,context):
    name = update.message.from_user.first_name
    print(str(update.effective_user.id))

    if trading_type == 'financial':
        msg = 'Hello ' + name + ', this is Bot SmartLever' + '\n' + \
              '  \n' + \
              'Available commands are: \n' + \
              '/start Start Bot.\n' + \
              '/mi_id Get Telegram ID\n' + \
              '/positions Current Positions. \n' + \
              '/status State of the Services. \n' + \
              '/prices Price of Symbols'

    elif trading_type == 'crypto':
        msg = 'Hello ' + name + ', this is Bot SmartLever' + '\n' + \
              '  \n' + \
              'Available commands are: \n' + \
              '/start Start Bot.\n' + \
              '/mi_id Get Telegram ID\n' + \
              '/positions Current Positions. \n' + \
              '/status State of the Services. \n' + \
              '/balance Get Wallet Balance'

    elif trading_type == 'betting':
        msg = 'Hello ' + name + ', this is Bot SmartLever' + '\n' + \
              '  \n' + \
              'Available commands are: \n' + \
              '/start Start Bot.\n' + \
              '/mi_id Get Telegram ID\n' + \
              '/status State of the Services. \n' + \
              '/balance Get Wallet Balance'

    _send_msg(msg=msg, chat_id=update.message.chat_id)

@restricted
def mi_id(update, context):
    """
    Return id
    """
    if update.message.chat_id not in LIST_OF_ADMINS:
        msg = 'Please send this id to the administrator.'
    else:
        msg = 'This is your id:'
    update.message.reply_text(msg)
    chat_id_str = str(update.message.chat_id)
    update.message.reply_text(str(chat_id_str))


def get_data_petition(name):
    for i in range(10):
        time.sleep(1)
        # check if name in list_symbols
        list_symbols = lib_petitions.list_symbols()
        if name in list_symbols:
            return lib_petitions.read(name).data
        time.sleep(5)


def create_petition(name_to_saving):
    function_to_run = 'get_saved_values_strategies_last'  # get_saved_values_strategy
    petition_pos = events.Petition(datetime=dt.datetime.now(), function_to_run=function_to_run,
                                   name_to_saving=name_to_saving, name_portfolio=name_portfolio)

    emiter.publish_event('petition', petition_pos)


@restricted
def balance(update, context):
    """
       Get balance from broker and get several statistics
    """
    try:
        if trading_type == 'crypto':
            current_balance = round(trading.get_total_balance('usd'), 2)
        elif trading_type == 'betting':
            current_balance = trading.get_account_funds()['availableToBetBalance']
        msg = '*Current Balance:*  ' + str(current_balance) + '\n'
        return_total = round(((current_balance - initial_balance) / initial_balance) * 100, 2)
        msg += '*Total Return:*  ' + str(return_total)
        _send_msg(msg=msg, chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        print(e)
        logger.error(f'Error getting balance: {e}')
        msg = 'Failed to get balance, please try again'
        _send_msg(msg=msg, chat_id=update.message.chat_id)


@restricted
def positions(update, context):
    """
    Return Positions
    """

    try:
        if trading_type == 'financial':
            # Get simulated positions
            name_to_saving = f'positions_{dt.datetime.now().strftime("%Y%m%d%H%M%S")}'
            # first create the petition
            create_petition(name_to_saving)
            # Get data Petition
            data_petition = get_data_petition(name_to_saving)
            # Agregate data_petition by ticker base
            agregate = {}
            tickers = []
            for _id in data_petition.keys():
                p = data_petition[_id]
                t = data_petition[_id]['ticker']
                if t not in tickers:
                    tickers.append(t)
                agregate.setdefault(t, 0)
                agregate[t] += p['position'] * p['quantity']
                agregate[t] = round(agregate[t], 2)

            # Get real positions
            lib_keeper = store.get_library(name_library)
            data = lib_keeper.read(symbol_positions).data
            broker_pos = data.positions
            trades = []
            for trade in agregate:
                real = 0
                if trade in broker_pos:
                    real = broker_pos[trade]
                trades.append([trade, real, agregate[trade]])
            msg = tabulate(trades,
                           headers=['Symbol', 'Real', 'Simulated'],
                           tablefmt='simple')
            _send_msg(msg=f"<pre>{msg}</pre>", chat_id=update.message.chat_id, parse_mode=ParseMode.HTML)

        elif trading_type == 'crypto':
            _broker_pos = trading.get_accounts()
            broker_pos = {c['currency']: float(c['balance']) for c in _broker_pos if
                          c['currency'] in symbols}
            msg = '*Current Positions:*' + '\n' + \
                  '' + str(broker_pos)
            _send_msg(msg=msg, chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        logger.error(f'Error getting Positions: {e}')
        msg = 'Failed to getting Positions, please try again'
        _send_msg(msg=msg, chat_id=update.message.chat_id)


@restricted
def status(update, context):
    """
    Send status of all Services
    """
    try:
        seconds = 300
        _health = _get_status(seconds=seconds)
        if len(_health) == 0:
            msg = 'All 👌, working in less than ' + str(seconds) + ' seconds'

        else:
            msg = _health

        _send_msg(msg=msg, chat_id=update.message.chat_id)

    except Exception as e:
        print(e)
        logger.error(f'Error getting service status: {e}')
        msg = 'Failed to get Status, please try again'
        _send_msg(msg=msg, chat_id=update.message.chat_id)


def _get_status(seconds=300):
    """
    Send health
    """
    try:
        lib_keeper = store.get_library(name_library)
        _health = {}
        _now = dt.datetime.utcnow()
        for service_name in list_services:
            # check if the service is running
            data = lib_keeper.read(service_name).data
            pn = service_name.replace('_health', '')
            _dtime = data.datetime
            state = data.state
            if _now >= _dtime:
                df_time = _now - _dtime
            else:
                df_time = _dtime - _now
            if abs(df_time.seconds) > seconds or state == 0:
                _health[pn] = {'last': str(_dtime), 'state': state}

        return _health
    except Exception as e:
        print(e)
        logger.error(f'Error getting service status: {e}')


@restricted
def prices(update, context):
    """
    Send Price
    """
    try:
        lib_keeper = store.get_library(name_library)
        now = dt.datetime.utcnow()
        initial_time = now.strftime("%Y-%m-%d 00:00:00")

        prices = []
        # Get price for each symbols
        for s in symbols:
            initial_price_symbol = f'{s}_{initial_time}_bar'
            initial_price_data = lib_keeper.read(initial_price_symbol).data
            initial_price = initial_price_data.close
            _range = range(0, 4, 1)
            # Check If the symbol exist
            for minute in _range:
                _now = now - dt.timedelta(minutes=minute)
                current_time = _now.strftime("%Y-%m-%d %H:%M:00")
                current_price_symbol = f'{s}_{current_time}_bar'
                if lib_keeper.has_symbol(current_price_symbol):
                    break
            # get current price
            current_price_data = lib_keeper.read(current_price_symbol).data
            current_price = current_price_data.close
            perc = round((current_price - initial_price) / initial_price * 100, 2)
            # Insert info to list
            prices.append([s, current_price, perc])

        msg = tabulate(prices,
                       headers=['Symbol', 'Price', 'Perc'],
                       tablefmt='simple')

        _send_msg(msg=f"<pre>{msg}</pre>", chat_id=update.message.chat_id, parse_mode=ParseMode.HTML)

    except Exception as e:
        print(e)
        logger.error(f'Error getting Price: {e}')
        msg = 'Failed to get price, please try again or no new data'
        _send_msg(msg=msg, chat_id=update.message.chat_id)


#  Controls
def callback_control():
    global name_library
    _time = dt.datetime.utcnow()
    name_library = f'{_name_library}_{_time.strftime("%Y%m%d")}'
    print('Checking controller  ' + str(_time))
    for k in counters_callback.keys():
        counters_callback[k] += 1

        if counters_callback['health'] >= 10:  # each 10 minutes
            """check every 10 minutes that the processes are running correctly"""
            try:
                print('Check health process  ' + str(_time))
                counters_callback['health'] = 0
                lib_keeper = store.get_library(name_library)
                for service_name in list_services:
                    # check if the service is running
                    try:
                        data = lib_keeper.read(service_name).data
                    except:
                        # not exist this service name in the DB
                        for user in LIST_OF_ADMINS:
                            # send alert
                            msg = 'ALERT, THIS SERVICE IS NOT WORKING: ' + str(service_name.replace('_health', ''))
                            _send_msg(msg=msg, chat_id=user)
                    datetime_service = data.datetime
                    # compare datetime_service with datetime current, if the difference is greater than 15 minutes, send alert
                    diff_minutes = abs((_time-datetime_service).seconds / 60)
                    if diff_minutes >= 15:
                        # send alert
                        for user in LIST_OF_ADMINS:
                            msg = 'ALERT, THIS SERVICE IS NOT WORKING: ' + str(service_name.replace('_health', ''))
                            _send_msg(msg=msg, chat_id=user)

            except Exception as ex:
                print(ex)
                logger.error(f'Error in callback_control health: {ex}')

        if counters_callback['positions'] >= 10 and trading_type in ['financial', 'crypto']:  # each 10 minutes
            """check every 10 minutes that simulation and real positions match"""
            try:
                print('Check positions ' + str(_time))
                counters_callback['positions'] = 0
                name_to_saving = f'positions_{dt.datetime.now().strftime("%Y%m%d%H%M%S")}'
                # first create the petition
                create_petition(name_to_saving)
                # Get data Petition
                data_petition = get_data_petition(name_to_saving)
                ## Agregate data_petition by ticker base
                agregate = {}
                tickers = []
                for _id in data_petition.keys():
                    p = data_petition[_id]
                    t = data_petition[_id]['ticker']
                    if t not in tickers:
                        tickers.append(t)
                    agregate.setdefault(t, 0)
                    agregate[t] += p['position'] * p['quantity']
                    agregate[t] = round(agregate[t], 2)

                if trading_type == 'financial':
                    lib_keeper = store.get_library(name_library)
                    data = lib_keeper.read(symbol_positions).data
                    broker_pos = data.positions
                elif trading_type == 'crypto':
                    list_currency = [c.split('-')[0] for c in agregate.keys()]
                    _broker_pos = trading.get_accounts()
                    broker_pos = {c['currency']: float(c['balance']) for c in _broker_pos if
                                  c['currency'] in list_currency}
                # check if positions is saving
                if _time > data.datetime:
                    diff_minutes = abs((_time - data.datetime).seconds / 60)
                    if diff_minutes > 4:
                        for user in LIST_OF_ADMINS:
                            msg = 'ALERT, Positions from mt4 is not saving'
                            _send_msg(msg=msg, chat_id=user)

                # Compute deference between broker and portfolio
                diference = {}
                for c in agregate.keys():
                    if c not in broker_pos:
                        quantity_broker = 0
                    else:
                        quantity_broker = broker_pos[c]
                    diference[c] = agregate[c] - quantity_broker
                    if diference[c] > 0:
                        diference[c] = round(diference[c], 2)
                    else:
                        diference[c] = round(diference[c], 2)

                send_alert = False
                for cu in diference:
                    if diference[cu] != 0:
                        send_alert = True
                if send_alert:
                    for user in LIST_OF_ADMINS:
                        msg = 'ALERT, simulation and real positions dont match: \n' + \
                              '' + str(diference)
                        _send_msg(msg=msg, chat_id=user)

            except Exception as ex:
                print(ex)
                logger.error(f'Error in callback_control positions: {ex}')


def error(update, error):
    """Log Errors caused by Updates."""
    today = dt.datetime.utcnow()
    event_telegram = {'date_time': today, 'comand': 'error', 'error': error}
    _send_msg(msg=event_telegram, chat_id=update.message.chat_id)


def schedule_callback_control():
    # create scheduler
    schedule.every(1).minutes.do(callback_control)
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    global LIST_OF_ADMINS, updater, counters_callback, name_library, _name_library, lib_keeper, store, list_services
    global lib_petitions, emiter, name_portfolio, symbol_positions, symbols, initial_balance, trading

    # initialize these variables to none
    name_portfolio = None
    symbol_positions = None
    symbols = None
    trading = None
    initial_balance = 0
    counters_callback = {'health': 0, 'positions': 0}
    if trading_type == 'financial':
        # token from telegram
        token = conf.TOKEN_TELEGRAM_FINANCIAL
        #  Parameters
        LIST_OF_ADMINS = conf.LIST_OF_ADMINS_FINANCIAL
        list_services = conf.LIST_SERVICES_FINANCIAL
        # name of portfolio which we want to know simulated positions
        name_portfolio = conf.NAME_FINANCIAL_PORTOFOLIO
        # symbol to read real positions from mongo
        symbol_positions = f'{conf.BROKER_FINANCIAL}_mt4_positions'
        # symbols to get price
        symbols = conf.FINANCIAL_SYMBOLS

    elif trading_type == 'crypto':
        # Create trading object to get info from broker
        trading = Trading(exchange=conf.BROKER_CRYPTO)
        # Parameters
        LIST_OF_ADMINS = conf.LIST_OF_ADMINS_CRYPTO
        list_services = conf.LIST_SERVICES_CRYPTO
        initial_balance = conf.INITIAL_BALANCE_CRYPTO
        symbols = conf.CRYPTO_SYMBOLS

    elif trading_type == 'betting':
        # Parameters
        token = conf.TOKEN_TELEGRAM_BETTING
        LIST_OF_ADMINS = conf.LIST_OF_ADMINS_BETTING
        list_services = conf.LIST_SERVICES_BETTING
        initial_balance = conf.INITIAL_BALANCE_BETTING
        # Create trading object to get info from broker
        trading = Trading()

    # Launch thread
    x = threading.Thread(target=schedule_callback_control)
    x.start()
    # Config DataBase
    _name_library = 'events_keeper'
    name_library = f'{_name_library}_{dt.datetime.utcnow().strftime("%Y%m%d")}'
    store = Universe(host=conf.MONGO_HOST, port=conf.MONGO_PORT)
    lib_keeper = store.get_library(name_library)
    lib_petitions = store.get_library('petitions')

    # Connection to broker mq
    config_brokermq = {'host': conf.RABBITMQ_HOST, 'port': conf.RABBITMQ_PORT, 'user': conf.RABBITMQ_USER,
                       'password': conf.RABBITMQ_PASSWORD}
    emiter = Emit_Events(config=config_brokermq)
    updater = Updater(token, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('status',
                                                  status))
    updater.dispatcher.add_handler(CommandHandler('mi_id',
                                                  mi_id))
    if trading_type == 'financial':
        updater.dispatcher.add_handler(CommandHandler('positions',
                                                      positions))
        updater.dispatcher.add_handler(CommandHandler('prices',
                                                      prices))
    elif trading_type == 'crypto':
        updater.dispatcher.add_handler(CommandHandler('balance',
                                                      balance))
        updater.dispatcher.add_handler(CommandHandler('positions',
                                                      positions))
    elif trading_type == 'betting':
        updater.dispatcher.add_handler(CommandHandler('balance',
                                                      balance))

    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    print(f'Running Telegram Bot {trading_type}')
    updater.idle()


if __name__ == '__main__':
    main()