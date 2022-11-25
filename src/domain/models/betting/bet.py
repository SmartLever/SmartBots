from dataclasses import dataclass
from dataclasses_json import dataclass_json
from src.domain.models.base import Base


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
    unique_name: str = None  # unique_name
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
    cancel_seconds: int = 120  # time to cancel bet, by default is 120 seconds

    def bet_prepare(self):
        """
        Create a dict with the parameter
        """
        bet_info = {'selectionId': str(self.selection_id)}
        if self.action == 'back':
            bet_info['side'] = 'BACK'
        else:
            bet_info['side'] = 'LAY'
        bet_info['orderType'] = 'LIMIT'
        bet_info['limitOrder'] = {'size': self.quantity, 'price': self.odds,
                                  'persistenceType': self.persistence_type}

        return [bet_info]
