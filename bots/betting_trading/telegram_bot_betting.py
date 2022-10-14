""" Telegram bot for Betting"""

from telegram.ext import Updater, CommandHandler
from functools import wraps
import threading
import datetime as dt
import time
from smartbots import conf
from telegram import ParseMode, ReplyKeyboardMarkup
from telegram.error import NetworkError, TelegramError
import schedule
from smartbots.database_handler import Universe
from smartbots.betting.betfair_model import Trading
from smartbots.base_logger import logger

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
            update.message.reply_text('You are not authorized, please talk to the administrator, id ' + str(user_id))
            logger.info("Unauthorized access denied for {}.".format(user_id))
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
def start(update, context):
    name = update.message.from_user.first_name
    print(str(update.effective_user.id))

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
    msg = 'Please send this id to the administrator.'
    update.message.reply_text(msg)
    chat_id_str = str(update.message.chat_id)
    update.message.reply_text(str(chat_id_str))

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
        logger.error(f'Error getting service status: {e}')

@restricted
def balance(update, context):
    """
       Get balance from broker and get several statistics
    """
    try:
        current_balance = trading.get_account_funds()['availableToBetBalance']
        msg = '*Current Balance:*  ' + str(current_balance) + '\n'
        return_total = round(((current_balance - initial_balance) / initial_balance) * 100, 2)
        msg += '*Total Return:*  ' + str(return_total)
        _send_msg(msg=msg, chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f'Error getting balance: {e}')


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
                logger.error(f'Error in callback_control health: {ex}')

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
    global initial_balance, trading

    #  Parameters
    # token from telegram
    token = conf.TOKEN_TELEGRAM_BETTING
    LIST_OF_ADMINS = []
    list_services = ['broker_betfair_health', 'data_realtime_provider_betfair_health']
    initial_balance = 100

    # Create trading object to get info from broker
    trading = Trading()
    # Launch thread
    x = threading.Thread(target=schedule_callback_control)
    x.start()
    counters_callback = {'health': 0}
    # Config DataBase
    _name_library = 'events_keeper'
    name_library = f'{_name_library}_{dt.datetime.utcnow().strftime("%Y%m%d")}'
    store = Universe()
    lib_keeper = store.get_library(name_library)

    updater = Updater(token, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('status',
                                                  status))
    updater.dispatcher.add_handler(CommandHandler('balance',
                                                  balance))
    updater.dispatcher.add_handler(CommandHandler('mi_id',
                                                  mi_id))

    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    print('Running Telegram Bot')
    updater.idle()


if __name__ == '__main__':
    main()