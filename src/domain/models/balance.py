from dataclasses import dataclass
from dataclasses_json import dataclass_json
from src.domain.models.base import Base


@dataclass_json
@dataclass
class Balance(Base):
    """ Balance """
    event_type: str = 'balance'
    ticker: str = 'balance'
    balance: float = None
    account: str = ''  # name of account

