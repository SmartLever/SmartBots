""" Create events with dataclasss as base.

    With dealing with date and time, events use datetime as base, for simplicity:
    datetime and datetime_epoch and dtime_zone are in all events, UTC is used as default, but
    datetime objet do not have timezone information.

"""
from dataclasses import dataclass
from dataclasses_json import dataclass_json
import datetime as dt

@dataclass_json
@dataclass
class Order:
    """ Event from Portfolio of Strategies to Exchange or Broker for execution """
    datetime: dt.datetime = None
    datetime_epoch: int = None
    dtime_zone: str = 'UTC'
    ticker: str = None
    contract: str = None
    action: str = None # buy or sell
    price: float = None
    quantity: float = None #quantity of contracts, amount always positive.
    quantity_execute: float = None #quantity of contracts executed, amount always positive.
    quantity_left: float = None #quantity of contracts left to execute, amount always positive.
    filled_price: float = None #price of executed contracts
    commission_fee: float = None #commission fee for executed contracts
    status: str = None #status of order
    exchange: str = None
    order_id_sender: str = None
    order_id_receiver: str = None
    datetime_in_epoch: int = None # datetime in epoch, broker or exchange enters the order


@dataclass_json
@dataclass
class Bar:
    """ Event from dataProvider to Portfolio of Strategies"""
    datetime: dt.datetime = None
    datetime_epoch: int = None
    dtime_zone: str = 'UTC'
    ticker: str = None
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
