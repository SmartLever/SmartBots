from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict, Any
from src.domain.models.base import Base


@dataclass_json
@dataclass
class Tick(Base):
    """ Tick event, generic case for data events """
    event_type: str = 'tick'
    tick_type: str = None  # closed_day, ask, bid, etc.
    price: float = None
    msg:  Dict[str, Any] = None
    description: str = None
