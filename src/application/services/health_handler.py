""" Manage if a services if running and working"""
from src.infraestructure.brokerMQ import Emit_Events
from src.domain.models.health import Health
import datetime as dt
import pytz


class Health_Handler():
    """ Manage if a services if running and working"""
    def __init__(self, n_check: int = 10, name_service: str = '', config: dict = {}):
        self.n_check = n_check # number of check before sending a event
        self.n = 0
        self.health = Health(ticker=name_service)
        self.emit = Emit_Events(config=config)

    def check(self):
        """ Add check to health event"""
        self.n += 1
        if self.n >= self.n_check: # send event
            self.send()
            self.n = 0

    def send(self, description:str ='', state: int =1):
        _d = dt.datetime.utcnow()
        dtime = dt.datetime(_d.year, _d.month, _d.day,
                            _d.hour, _d.minute, _d.second, 0, pytz.UTC)
        self.health.datetime = dtime
        self.health.state = state
        self.health.description = description
        self.emit.publish_event('health', self.health)


