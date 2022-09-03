""" Create events with dataclasss as base.

    With dealing with date and time, events use datetime as base, for simplicity:
    datetime and datetime_epoch and dtime_zone are in all events, UTC is used as default, but
    datetime objet do not have timezone information.

"""
from dataclasses import dataclass
from dataclasses_json import dataclass_json
import datetime as dt
from typing import List, Dict, Any, Optional, Union

@dataclass_json
@dataclass
class Base:
    """ Base class for events """
    event_type: str = 'petition'
    datetime: dt.datetime = None
    dtime_zone: str = 'UTC'
    ticker: str = None

@dataclass_json
@dataclass
class Tick(Base):
    """ Tick event, generic case for data events """
    event_type: str = 'tick'
    tick_type: str = None # closed_day, ask, bid, etc.
    price: float = None
    msg:  Dict[str, Any] = None
    description: str = None

@dataclass_json
@dataclass
class Petition(Base):
    """ Petition for getting data from a data source from running processes """
    event_type: str = 'petition'
    ticker: str = 'petition'
    function_to_run: str = None # petition of function to run for the petition
    parameters: Dict[str, Any] = None # parameters for the function to run
    path_to_saving: str = 'petitions' # path to saving the data
    name_to_saving: str = 'default' # name of the key to save the data

@dataclass_json
@dataclass
class Health(Base):
    """ Health event for getting if the process ir running """
    event_type: str = 'health'
    ticker: str = 'Health_Process' # process for controling
    state: int = 1 # 0 not_working and 1 working
    description: str = '' # description in case is not working, could be a exception


####Financial and crypto events##################################################################
@dataclass_json
@dataclass
class Order(Base):
    """ Event from Portfolio of Strategies to Exchange or Broker for execution """
    event_type: str = 'order'
    contract: str = None
    action: str = None # buy or sell
    price: float = None
    type: str = None # market or limit
    quantity: float = None #quantity of contracts, amount always positive.
    quantity_execute: float = None #quantity of contracts executed, amount always positive.
    quantity_left: float = None #quantity of contracts left to execute, amount always positive.
    filled_price: float = None #price of executed contracts
    commission_fee: float = None #commission fee for executed contracts
    fee_currency: str = None #currency of commission fee
    status: str = None #status of order, open, closed, cancelled
    exchange: str = None
    order_id_sender: str = None
    order_id_receiver: str = None
    datetime_in: dt.datetime = None # datetime when in broker or exchange enters the order
    sender_id: int = None # id of sender, strategies id
    portfolio_name: str = None # name of portfolio
    error_description: str = None # error description if error

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

######################### Betting events ##############################################################
@dataclass_json
@dataclass
class Odds(Base):
    """ Event from dataProvider of betting exchange to Portfolio of Strategies
    For maintening ticker as main conductor as in Finance and Crypto, ticker here is equal to event type.
    """
    event_type: str = 'odds'
    datetime_real_off: dt.datetime = None  # real time of the event
    datetime_scheduled_off: dt.datetime = None  # scheduled time of the event
    datatime_latest_taken: dt.datetime = None  # real time from betfair where the bets was matched
    unique_name: str = None  # unique for ticker and match, for example: albacete vs betis_1_over/under 2.5 goals_202201010820
    unique_id_match: str = None  # unique id for the match
    unique_id_ticker: str = None  # unique id for the event
    selection: str = None  # selection type, for example: under 2.5 goals
    selection_id: int = None  # selection id
    ticker_id: float = None  # event id
    competition: str = None
    days_since_last_run: int = None  # days since last run, for horse racing
    match_name: str = None  # match name
    local_team: str = None  # local team
    away_team: str = None  # away team
    full_description: str = None  # full description
    competition_id: int = None  # id of the competition
    last_row: int = None  # last row of data
    local_team_id: int = None  # id of the local team
    away_team_id: int = None  # id of the away team
    match_id: int = None  # id of the match
    in_play: bool = None  # in play
    jockey_name: str = None  # jockey name
    odds_last_traded: float = None  # last price traded
    number_of_active_runners: int = None  # number of active runners
    number_of_winners: int = None  # number of winners
    odds_back: List[float] = None  # back odds
    odds_lay: List[float] = None  # lay odds
    size_back: List[float] = None  # back size odds
    size_lay: List[float] = None  # lay size odds
    official_rating: float = None  # official rating
    player_name: str = None  # player name
    trainer_name: str = None  # trainer name
    sex_type: str = None
    sort_priority: int = None
    sports_id: int = None
    status: str = None  # closed, open
    status_selection: str = None  # active, winner, loser
    volume_matched: float = None
    win_flag: bool = None  # win flag


@dataclass_json
@dataclass
class Bet(Base):
    """ Event from Portfolio of Strategies to Exchange of betting for execution """
    event_type: str = 'bet'
    ticker_id: float = None  # event id
    selection: str = None  # selection type
    selection_id: int = None  # selection id
    action: str = None  # back or lay
    odds: float = None  # odds
    quantity: float = None  # quantity for betting
    match_name: str = None  # match name
    quantity_execute: float = None  # quantity executed, amount always positive.
    quantity_left: float = None  # quantity of contracts left to execute, amount always positive.
    filled_price: float = None  # price of executed contracts
    commission_fee: float = None  # commission fee for executed contracts
    bet_id: float = None  # bet_id
    status: str = None  # status of order
    persistence_type: str = 'PERSIST'  # 'LAPSE', 'PERSIST' or 'MARKET_ON_CLOSE'
    bet_type: str = 'LIMIT'  # options = 'LIMIT', 'LIMIT_ON_CLOSE' or 'MARKET_ON_CLOSE'
    id_sender: int = None  # id of sender, strategies id
    portfolio_name: str = None  # name of portfolio
    error_description: str = None  # error description if error

    def bet_prepare(self):
        """
        Create a dict with the parameter
        """
        bet_info = {'selectionId': self.selection_id}
        if self.action == 'back':
            bet_info['side'] = 'BACK'
        else:
            bet_info['side'] = 'LAY'
        bet_info['orderType'] = 'LIMIT'
        bet_info['limitOrder'] = {'size': self.quantity, 'price': self.odds,
                                  'persistenceType': self.persistence_type}

        return bet_info
