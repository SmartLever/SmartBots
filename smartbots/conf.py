import os
from dotenv import load_dotenv
import ast


path = os.path.abspath(__file__)
path_modulo = os.path.dirname(path)  # path to the module
path_to_principal = path_modulo.replace('smartbots','')
path_to_crypto = os.path.join(path_modulo, 'crypto')
path_to_betting = os.path.join(path_modulo, 'betting')
path_to_financial = os.path.join(path_modulo, 'financial')

# create folders for code your strategies
path_to_my_strategies = os.path.join(path_to_crypto, 'strategies')
path_to_my_strategies_betting = os.path.join(path_to_betting, 'strategies')
if not os.path.exists(path_to_my_strategies):
    os.makedirs(path_to_my_strategies)
if not os.path.exists(path_to_my_strategies_betting):
    os.makedirs(path_to_my_strategies_betting)

path_to_temp = os.path.join(path_modulo, 'temp')
# Check is exist temp folder
if not os.path.exists(path_to_temp):
    os.makedirs(path_to_temp)

# Create folders for my strategies
patha_to_my_smartbots = os.path.join(path_to_principal, 'my_smartbots')
path_to_my_strategies = {}
path_to_my_strategies['crypto'] = os.path.join(patha_to_my_smartbots, 'my_crypto_strategies')
path_to_my_strategies['financial']  = os.path.join(patha_to_my_smartbots, 'my_financial_strategies')
path_to_my_strategies['betting']= os.path.join(patha_to_my_smartbots, 'my_betting_strategies')

if not os.path.exists(patha_to_my_smartbots):
    os.makedirs(patha_to_my_smartbots)

for key in path_to_my_strategies:
    if not os.path.exists(path_to_my_strategies[key]):
        os.makedirs(path_to_my_strategies[key])



if os.getenv('AM_I_IN_A_DOCKER_CONTAINER') == '1': # only with docker running
    # Path to docker folder
    load_dotenv(os.path.join(path_to_principal,'docker', "compose.env"))
else:
    load_dotenv(os.path.join(path_to_principal, "conf.env"))

# MongoDB
MONGO_HOST= os.getenv("MONGO_HOST") or "REPLACE_ME"
MONGO_PORT= os.getenv("MONGO_PORT") or "REPLACE_ME"


# BrokerMQ
RABBITMQ_USER = os.getenv("RABBITMQ_USER") or "REPLACE_ME"
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD") or "REPLACE_ME"
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST") or "REPLACE_ME"
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT") or "REPLACE_ME"

# https://www.kucoin.com/
API_KUCOIN_API_KEYS = os.getenv("API_KUCOIN_API_KEYS") or "REPLACE_ME"
API_KUCOIN_API_SECRET = os.getenv("API_KUCOIN_API_SECRET") or "REPLACE_ME"
API_KUCOIN_API_PASSPHRASE = os.getenv("API_KUCOIN_API_PASSPHRASE") or "REPLACE_ME"

# betfair
USERNAME_BETFAIR = os.getenv("USERNAME_BETFAIR") or "REPLACE_ME"
PASSWORD_BETFAIR = os.getenv("PASSWORD_BETFAIR") or "REPLACE_ME"
APP_KEYS_BETFAIR = os.getenv("APP_KEYS_BETFAIR") or "REPLACE_ME"

# Variable for production
SEND_ORDERS_BROKER_KUCOIN = int(os.getenv("SEND_ORDERS_BROKER_KUCOIN")) or 0
SEND_ORDERS_BROKER_DARWINEX = int(os.getenv("SEND_ORDERS_BROKER_DARWINEX")) or 0

# Telegram
TOKEN_TELEGRAM_BETTING = os.getenv("TOKEN_TELEGRAM_BETTING") or "REPLACE_ME"
TOKEN_TELEGRAM_CRYPTO = os.getenv("TOKEN_TELEGRAM_CRYPTO") or "REPLACE_ME"
TOKEN_TELEGRAM_FINANCIAL = os.getenv("TOKEN_TELEGRAM_FINANCIAL") or "REPLACE_ME"

# Info Darwinex
DARWINEX_HOST = os.getenv("DARWINEX_HOST") or "REPLACE_ME"
CLIENT_IF = os.getenv("CLIENT_IF") or "REPLACE_ME"
PUSH_PORT = os.getenv("PUSH_PORT") or "REPLACE_ME"
PULL_PORT_PROVIDER = os.getenv("PULL_PORT_PROVIDER") or "REPLACE_ME"
PULL_PORT_BROKER = os.getenv("PULL_PORT_BROKER") or "REPLACE_ME"
SUB_PORT_PROVIDER = os.getenv("SUB_PORT_PROVIDER") or "REPLACE_ME"
SUB_PORT_BROKER = os.getenv("SUB_PORT_BROKER") or "REPLACE_ME"
FINANCIAL_SYMBOLS = os.getenv("FINANCIAL_SYMBOLS") or "REPLACE_ME"
# is a list
if '[' in FINANCIAL_SYMBOLS:
    FINANCIAL_SYMBOLS = ast.literal_eval(FINANCIAL_SYMBOLS)

PERCENTAGE_CLOSE_POSITIONS_DARWINEX = os.getenv("PERCENTAGE_CLOSE_POSITIONS_DARWINEX") or None

# Info Webhook
WEBHOOKS = {}
WEBHOOKS['TRADINGVIEW_KEY'] = os.getenv("WEBHOOKS_TRADINGVIEW_KEY") or "REPLACE_ME"

# Credential ftp to download data historical from Darwinex
DWT_FTP_USER = os.getenv("DWT_FTP_USER") or "REPLACE_ME"
DWT_FTP_PASS = os.getenv("DWT_FTP_PASS") or "REPLACE_ME"
DWT_FTP_HOSTNAME = os.getenv("DWT_FTP_HOSTNAME") or "REPLACE_ME"
DWT_FTP_PORT = os.getenv("DWT_FTP_PORT") or "REPLACE_ME"
