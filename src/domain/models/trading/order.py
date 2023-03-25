from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
import datetime as dt
from datetime import datetime
from src.domain.models.base import Base

dataclass_json_config = config(
            decoder=datetime.utcfromtimestamp,
        )


@dataclass_json
@dataclass
class Order(Base):
    """ Event from Portfolio of Strategies to Exchange or Broker for execution """
    event_type: str = 'order'
    contract: str = None
    action: str = None  # buy or sell
    price: float = None
    type: str = None  # market or limit
    quantity: float = None  # quantity of contracts, amount always positive.
    quantity_execute: float = None  # quantity of contracts executed, amount always positive.
    quantity_left: float = None  # quantity of contracts left to execute, amount always positive.
    filled_price: float = None  # price of executed contracts
    commission_fee: float = None  # commission fee for executed contracts
    fee_currency: str = None  # currency of commission fee
    status: str = None  # status of order, open, closed, cancelled
    exchange: str = None
    order_id_sender: str = None
    order_id_receiver: str = None
    trace_id: str = None
    datetime_in: dt.datetime = field(default=None, metadata=dataclass_json_config)
    sender_id: int = None  # id of sender, strategies id
    portfolio_name: str = None  # name of portfolio
    error_description: str = None  # error description if error
    action_mt4: str = None  # close_trade, close_partial, normal
    duration: str = 'DAY'
    account: str = ''  # name of account
