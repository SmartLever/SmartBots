import os
from dotenv import load_dotenv
import ast
from pathlib import Path


path = Path(__file__).resolve()
path_modulo = path.parent.parent  # path to the module
path_to_principal = path_modulo.parent

path_to_temp = os.path.join(path_modulo, 'application', 'temp')
path_to_data = os.path.join(path_modulo, 'application', 'data')
# Check is exist temp folder
if not os.path.exists(path_to_temp):
    os.makedirs(path_to_temp)

# Check is exist data folder for test_data
path_to_test_data = os.path.join(path_to_data, 'test_data')
if not os.path.exists(path_to_test_data):
    os.makedirs(path_to_test_data)


if os.getenv('AM_I_IN_A_DOCKER_CONTAINER') == '1': # only with docker running
    # Path to docker folder
    load_dotenv(os.path.join(path_to_principal, 'docker', "compose.env"))
else:
    load_dotenv(os.path.join(path_to_principal, "conf.env"))

# folders for my strategies
path_to_my_smartbots = os.getenv('MY_SMARTBOTS_PATH')
path_to_my_strategies = {}
path_to_my_strategies['financial'] = os.path.join(path_to_my_smartbots, 'my_financial_strategies')
path_to_my_strategies['betting' ]= os.path.join(path_to_my_smartbots, 'my_betting_strategies')


######### COMMON PARAMETERS ######################

# MongoDB
MONGO_HOST = os.getenv("MONGO_HOST") or "REPLACE_ME"
MONGO_PORT = os.getenv("MONGO_PORT") or "REPLACE_ME"

# BrokerMQ
RABBITMQ_USER = os.getenv("RABBITMQ_USER") or "REPLACE_ME"
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD") or "REPLACE_ME"
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST") or "REPLACE_ME"
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT") or "REPLACE_ME"

# Info Webhook
WEBHOOKS = {}
WEBHOOKS['TRADINGVIEW_KEY'] = os.getenv("WEBHOOKS_TRADINGVIEW_KEY") or "REPLACE_ME"

# type of trading in telegram
TRADING_TYPE_TELEGRAM = os.getenv("TRADING_TYPE_TELEGRAM") or "REPLACE_ME"

# channel where orders are received just for financial and crypto
if 'ROUTING_KEY' in os.environ: #docker
    ROUTING_KEY = os.environ['ROUTING_KEY']
else:
    ROUTING_KEY = os.getenv("ROUTING_KEY") or "order"

# config of porfolio
if 'CONF_PORTFOLIO' in os.environ: #docker
    CONF_PORTFOLIO = os.environ['CONF_PORTFOLIO']
else:
    CONF_PORTFOLIO = os.getenv("CONF_PORTFOLIO") or "config_financial"

# asset_type
if 'ASSET_TYPE' in os.environ: #docker
    ASSET_TYPE = os.environ['ASSET_TYPE']
else:
    ASSET_TYPE = os.getenv("ASSET_TYPE") or "financial"

##################################################


######### BETTING PARAMETERS ######################

# betfair
USERNAME_BETFAIR = os.getenv("USERNAME_BETFAIR") or "REPLACE_ME"
PASSWORD_BETFAIR = os.getenv("PASSWORD_BETFAIR") or "REPLACE_ME"
APP_KEYS_BETFAIR = os.getenv("APP_KEYS_BETFAIR") or "REPLACE_ME"
BROKER_BETTING = os.getenv("BROKER_BETTING") or "betfair"
# Telegram
TOKEN_TELEGRAM_BETTING = os.getenv("TOKEN_TELEGRAM_BETTING") or "REPLACE_ME"
LIST_OF_ADMINS_BETTING = os.getenv("LIST_OF_ADMINS_BETTING") or "REPLACE_ME"
# is a list
if '[' in LIST_OF_ADMINS_BETTING:
    LIST_OF_ADMINS_BETTING = ast.literal_eval(LIST_OF_ADMINS_BETTING)

LIST_SERVICES_BETTING = os.getenv("LIST_SERVICES_BETTING") or "REPLACE_ME"
# is a list
if '[' in LIST_SERVICES_BETTING:
    LIST_SERVICES_BETTING = ast.literal_eval(LIST_SERVICES_BETTING)
INITIAL_BALANCE_BETTING = os.getenv("INITIAL_BALANCE_BETTING") or "REPLACE_ME"


##################################################


######### FINANCIAL PARAMETERS ######################

# Variable for production
SEND_ORDERS_BROKER_MT4 = int(os.getenv("SEND_ORDERS_BROKER_MT4")) or 0

# Telegram
TOKEN_TELEGRAM_FINANCIAL = os.getenv("TOKEN_TELEGRAM_FINANCIAL") or "REPLACE_ME"

# Info Darwinex
if 'MT4_HOST' in os.environ: #docker
    MT4_HOST = os.environ['MT4_HOST']
else:
    MT4_HOST = os.getenv("MT4_HOST") or "REPLACE_ME"
CLIENT_IF = os.getenv("CLIENT_IF") or "REPLACE_ME"
PUSH_PORT = os.getenv("PUSH_PORT") or "REPLACE_ME"
PULL_PORT_PROVIDER = os.getenv("PULL_PORT_PROVIDER") or "REPLACE_ME"
PULL_PORT_BROKER = os.getenv("PULL_PORT_BROKER") or "REPLACE_ME"
SUB_PORT_PROVIDER = os.getenv("SUB_PORT_PROVIDER") or "REPLACE_ME"
SUB_PORT_BROKER = os.getenv("SUB_PORT_BROKER") or "REPLACE_ME"
FINANCIAL_SYMBOLS = os.getenv("FINANCIAL_SYMBOLS") or "REPLACE_ME"  # Symbols to get real data
# is a list
if '[' in FINANCIAL_SYMBOLS:
    FINANCIAL_SYMBOLS = ast.literal_eval(FINANCIAL_SYMBOLS)

PERCENTAGE_CLOSE_POSITIONS_MT4 = os.getenv("PERCENTAGE_CLOSE_POSITIONS_MT4") or None
# Name of the Portfolio which is running in production
if 'NAME_FINANCIAL_PORTOFOLIO' in os.environ: #docker
    NAME_FINANCIAL_PORTOFOLIO = os.environ['NAME_FINANCIAL_PORTOFOLIO']
else:
    NAME_FINANCIAL_PORTOFOLIO = os.getenv("NAME_FINANCIAL_PORTOFOLIO") or "NAME_FINANCIAL_PORTOFOLIO"
if 'BROKER_FINANCIAL' in os.environ:  # Name of the broker-mt4, you are going to connect
    BROKER_FINANCIAL = os.environ['BROKER_FINANCIAL']
else:
    BROKER_FINANCIAL = os.getenv("BROKER_FINANCIAL") or "REPLACE_ME"
LIST_SERVICES_FINANCIAL = os.getenv("LIST_SERVICES_FINANCIAL") or "REPLACE_ME"
# is a list
if '[' in LIST_SERVICES_FINANCIAL:
    LIST_SERVICES_FINANCIAL = ast.literal_eval(LIST_SERVICES_FINANCIAL)

LIST_OF_ADMINS_FINANCIAL = os.getenv("LIST_OF_ADMINS_FINANCIAL") or "REPLACE_ME"
# is a list
if '[' in LIST_OF_ADMINS_FINANCIAL:
    LIST_OF_ADMINS_FINANCIAL = ast.literal_eval(LIST_OF_ADMINS_FINANCIAL)
    
# Credential ftp to download data historical from Darwinex
DWT_FTP_USER = os.getenv("DWT_FTP_USER") or "REPLACE_ME"
DWT_FTP_PASS = os.getenv("DWT_FTP_PASS") or "REPLACE_ME"
DWT_FTP_HOSTNAME = os.getenv("DWT_FTP_HOSTNAME") or "REPLACE_ME"
DWT_FTP_PORT = os.getenv("DWT_FTP_PORT") or "REPLACE_ME"

##################################################


######### CRYPTO PARAMETERS ######################

# https://www.kucoin.com/
API_KUCOIN_API_KEYS = os.getenv("API_KUCOIN_API_KEYS") or "REPLACE_ME"
API_KUCOIN_API_SECRET = os.getenv("API_KUCOIN_API_SECRET") or "REPLACE_ME"
API_KUCOIN_API_PASSPHRASE = os.getenv("API_KUCOIN_API_PASSPHRASE") or "REPLACE_ME"

# Variable for production
SEND_ORDERS_BROKER_KUCOIN = int(os.getenv("SEND_ORDERS_BROKER_KUCOIN")) or 0

# Telegram
TOKEN_TELEGRAM_CRYPTO = os.getenv("TOKEN_TELEGRAM_CRYPTO") or "REPLACE_ME"
LIST_OF_ADMINS_CRYPTO = []
LIST_SERVICES_CRYPTO = os.getenv("LIST_SERVICES_CRYPTO") or "REPLACE_ME"
# is a list
if '[' in LIST_SERVICES_CRYPTO:
    LIST_SERVICES_CRYPTO = ast.literal_eval(LIST_SERVICES_CRYPTO)

LIST_OF_ADMINS_CRYPTO = os.getenv("LIST_OF_ADMINS_CRYPTO") or "REPLACE_ME"
# is a list
if '[' in LIST_OF_ADMINS_CRYPTO:
    LIST_OF_ADMINS_CRYPTO = ast.literal_eval(LIST_OF_ADMINS_CRYPTO)

CRYPTO_SYMBOLS = os.getenv("CRYPTO_SYMBOLS") or "REPLACE_ME"  # Symbols to get real data
# is a list
if '[' in CRYPTO_SYMBOLS:
    CRYPTO_SYMBOLS = ast.literal_eval(CRYPTO_SYMBOLS)
INITIAL_BALANCE_CRYPTO = os.getenv("INITIAL_BALANCE_CRYPTO") or 100
BROKER_CRYPTO = os.getenv("BROKER_CRYPTO") or "REPLACE_ME"

##################################################
