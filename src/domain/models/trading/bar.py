from dataclasses import dataclass
from dataclasses_json import dataclass_json, config
from datetime import datetime
from src.domain.models.base import Base

dataclass_json_config = config(
            decoder=datetime.utcfromtimestamp,
        )


@dataclass_json
@dataclass
class Bar(Base):
    """ Event from dataProvider to Portfolio of Strategies"""
    event_type:str = 'bar'
    open: float = None
    high: float = None
    low: float = None
    close: float = None
    volume: float = 0.0
    open_interest: float = None  # open interest
    bid: float = None  # Bid price
    ask: float = None  # Ask price
    multiplier: float = 1  # in case of futures
    contract_size: float = None  # in case of futures
    contract_month_year: int = None  # in case of futures, for example: 201912
    contract: str = None  # in case of futures, for example: FU201912
    freq: str = None  # frequency of the bar, example: "1m","30m" "1h", "1d", "1w", "1M", "1Y"
    exchange: str = None  # exchange of the bar
    currency: str = None  # currency of the bar
    provider: str = None  # provider of the bar, example: "binance", "bitmex", "oanda", "fxcm", "interactivebrokers", "dukascopy"
    type_bar: str = None  # type of the bar, example: "FUT", "FX", "CRYPTO", "STOCK", "INDEX"
