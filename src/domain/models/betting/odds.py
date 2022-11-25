from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from datetime import datetime
from src.domain.models.base import Base
import datetime as dt
from typing import List
dataclass_json_config = config(
            decoder=datetime.utcfromtimestamp,
        )


@dataclass_json
@dataclass
class Odds(Base):
    """ Event from dataProvider of betting exchange to Portfolio of Strategies
    For maintening ticker as main conductor as in Finance and Crypto, ticker here is equal to event type.
    """
    event_type: str = 'odds'
    datetime_real_off: dt.datetime = field(default=None, metadata=dataclass_json_config)  # real time of the event
    datetime_scheduled_off: dt.datetime = field(default=None, metadata=dataclass_json_config)  # scheduled time of the event
    datatime_latest_taken: dt.datetime = field(default=None, metadata=dataclass_json_config)  # real time from betfair where the bets was matched
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
