import logging
from os.path import join
from pathlib import Path
from src.application import conf


path_log = join(conf.path_to_temp, 'data.log')
logging.basicConfig(filename=path_log, filemode='w', format='%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger(__name__)