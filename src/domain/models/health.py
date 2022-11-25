from dataclasses import dataclass
from dataclasses_json import dataclass_json
from src.domain.models.base import Base


@dataclass_json
@dataclass
class Health(Base):
    """ Health event for getting if the process ir running """
    event_type: str = 'health'
    ticker: str = 'Health_Process' # process for controling
    state: int = 1  # 0 not_working and 1 working
    description: str = ''  # description in case is not working, could be a exception
