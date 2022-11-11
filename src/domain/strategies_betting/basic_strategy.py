""" Basic strategic for testing purposes, Back and Lay at entry time """
from src.domain.abstractions.abstract_strategy import Abstract_Strategy, dataclass

class Basic_Strategy(Abstract_Strategy):
    def __init__(self, params, id_strategy=None, callback=None, set_basic=False):
        super().__init__(params, id_strategy, callback, set_basic)
        parameters = params
        self.selection = parameters['selection']
        self.action = parameters['action']  # action
        self.init_odd = parameters['init_odd']  # init_odd
        self.end_odd = parameters['end_odd']  # end_odd
        self.init_time = parameters['init_time']  # init_time
        self.end_time = parameters['end_time']  # end_time
        self.type_trading = 'betting'
        if 'cancel_seconds' not in parameters:
            self.cancel_seconds = 100
        else:
            self.cancel_seconds = parameters['cancel_seconds']  # cancel_seconds
        self.diff_odds = parameters['diff_odds']
        self.id_strategy = id_strategy
        # Parameters for unique events
        self.n_events = {}  # dict with unique as key and number of events as value
        self.unique_control = {}  # dict with unique as key and true or false as value
        self.saves_values = []  # list of bets

    def _fill_unique_data(self, unique: str):
        """ Fill the unique data for event type"""
        self.unique_control[unique] = True
        self.n_events[unique] = 0

    def _time_conditions(self, odds: dataclass):
        """ Check if the event is between the times parameters"""
        from_init = (odds.datatime_latest_taken - odds.datetime_real_off).seconds / 60
        # check range time
        if self.init_time <= from_init <= self.end_time:
            return True
        return False

    def check_control_unique(self, unique: str):
        """ Check if the event is unique """
        if unique not in self.unique_control:
            self.unique_control[unique] = True
            self._fill_unique_data(unique)
            return True
        else:
            return False

    def get_saved_values(self):
        """ Return values saved """
        return self.saves_values

    def add_event(self, odds: dataclass):
        """ Add event to the strategy and apply logic """
        # status is open
        if odds.selection == self.selection:
            unique = odds.unique_name
            self.check_control_unique(unique)
            if self.n_events[unique] == 0:
                # check is the odds_last_traded has value
                if odds.odds_last_traded is not None:
                    if abs(odds.odds_back[0] - odds.odds_lay[0]) <= self.diff_odds:
                        if self._time_conditions(odds):
                            # check is the odds_last_traded is between the odds parameters
                            if self.end_odd >= odds.odds_last_traded >= self.init_odd:
                                # just one bet for event
                                self.n_events[unique] += 1
                                self.send_order(datetime=odds.datetime, ticker=self.ticker,
                                                selection=odds.selection, price=odds.odds_last_traded,
                                                quantity=self.quantity,
                                                match_name=odds.match_name, ticker_id=odds.ticker_id,
                                                selection_id=odds.selection_id, action=self.action,
                                                cancel_seconds=self.cancel_seconds, unique_name=odds.unique_name)


