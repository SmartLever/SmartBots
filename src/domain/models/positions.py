from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict, Any
from src.domain.models.base import Base


@dataclass_json
@dataclass
class Positions(Base):
    """ Real Positions """
    event_type: str = 'positions'
    ticker: str = 'Real_positions'
    positions: Dict[str, Any] = None
    account: str = ''  # name of account
