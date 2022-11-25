from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict, Any
from src.domain.models.base import Base


@dataclass_json
@dataclass
class WebHook(Base):
    """ WebHook event"""
    event_type: str = 'webhook'
    hook_type: str = None  # indicator, strategy
    msg:  Dict[str, Any] = None

