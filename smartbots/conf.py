import os
from dotenv import load_dotenv


path = os.path.abspath(__file__)
path_modulo = os.path.dirname(path)  # path to the module
path_to_principal = path_modulo.replace('smartbots','')

path_to_temp = os.path.join(path_modulo, 'temp')
# Check is exist temp folder
if not os.path.exists(path_to_temp):
    os.makedirs(path_to_temp)


if  os.getenv('AM_I_IN_A_DOCKER_CONTAINER') == '1': # only with docker running
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

