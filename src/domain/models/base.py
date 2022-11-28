""" Base class for models """

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
import datetime as dt
from datetime import datetime

dataclass_json_config = config(
            decoder=datetime.utcfromtimestamp,
        )


@dataclass_json
@dataclass
class Base:
    """ Base class for events """
    event_type: str = 'base'
    datetime: dt.datetime = field(default=None, metadata=dataclass_json_config)
    dtime_zone: str = 'UTC'
    ticker: str = None
