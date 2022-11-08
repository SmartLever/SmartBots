""" Classe Handler for database
The database is MongoDB and use Arctic management for storing data.
More info hear: https://arctic.readthedocs.io/en/latest/index.html

"""
import logging
from arctic import Arctic
from arctic import TICK_STORE
from arctic import CHUNK_STORE
from smartbots import conf
from smartbots.decorators import log_start_end, check_api_key


logger = logging.getLogger(__name__)

# Decorator for checking API key
@log_start_end(log=logger)
@check_api_key(
    [
        "MONGO_HOST",
        "MONGO_PORT"
    ]
)
def get_client():
    # Conection to the database
    return Arctic(f'{conf.MONGO_HOST}:{conf.MONGO_PORT}')


class Universe():
    """ Universe is the database handler"""
    def __init__(self):
        self.client = get_client()

    def get_library(self, name_library, library_chunk_store=True):
        if not self.client.library_exists(name_library):
            if library_chunk_store:
                self.client.initialize_library(name_library, lib_type=CHUNK_STORE)
            else:
                self.client.initialize_library(name_library)
        return self.client[name_library]