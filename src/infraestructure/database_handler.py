""" Classe Handler for database
The database is MongoDB and use Arctic management for storing data.
More info hear: https://arctic.readthedocs.io/en/latest/index.html

"""
import logging
from arctic import Arctic
from arctic import CHUNK_STORE
from src.domain.decorators import log_start_end, check_api_key


logger = logging.getLogger(__name__)

# Decorator for checking API key
@log_start_end(log=logger)
def get_client(host=None, port=None):
    # Conection to the database
    return Arctic(f'{host}:{port}')


class Universe():
    """ Universe is the database handler"""
    def __init__(self, host=None, port=None):
        self.client = get_client(host=host, port=port)

    def get_library(self, name_library, library_chunk_store=True):
        if not self.client.library_exists(name_library):
            if library_chunk_store:
                self.client.initialize_library(name_library, lib_type=CHUNK_STORE)
            else:
                self.client.initialize_library(name_library)
        return self.client[name_library]