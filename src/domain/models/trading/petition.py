from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict, Any
from src.domain.models.base import Base


@dataclass_json
@dataclass
class Petition(Base):
    """ Petition for getting data from a data source from running processes """
    event_type: str = 'petition'
    ticker: str = 'petition'
    function_to_run: str = None  # petition of function to run for the petition
    parameters: Dict[str, Any] = None  # parameters for the function to run
    path_to_saving: str = 'petitions'  # path to saving the data
    name_to_saving: str = 'default'  # name of the key to save the data
    name_portfolio: str = None
