""" Wrapper around MQ broker, using Rabbitmq
LocalHost: http://localhost:15672/
"""
import time
import pika
import json
import logging
from src.domain.decorators import log_start_end
from src.domain.models.trading import bar, tick, timer, order, webhook, petition
from src.domain.models.betting import odds, bet
from src.domain.models import health, positions
from dataclasses import dataclass
import datetime as dt
import pytz
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

events_type = {'bar': bar.Bar, 'order': order.Order, 'petition': petition.Petition,
               'health': health.Health, 'tick': tick.Tick, 'odds': odds.Odds, 'bet': bet.Bet,
               'financial_order': order.Order, 'positions': positions.Positions, 'order_status': order. Order,
               'timer': timer.Timer, 'webhook': webhook.WebHook}  #define types of events


logger = logging.getLogger(__name__)


def _callback(ch, method, properties, body):
    print(" [x] %r:%r" % (method.routing_key, json.loads(body)))


class CallBack_Handler(object):
    """ Callback Handler for transforming msg from MQ to events"""
    def __init__(self, callback: callable=None):
        if callback is None:
            self.callback = self._callback_default
        else:
            self.callback = callback

    def _callback_default(self, event: dataclass):
        print(event)

    def callback_recieved(self, ch, method, properties, body):
        """ Callback function for realtime data"""
        routing_key = method.routing_key
        # check if order type
        if '_order' in routing_key:
            routing_key = 'order'
        event = events_type[routing_key].from_json(body)
        if 'datetime' in event.__dict__:
            if event.datetime is not None:
                _dtime = event.datetime
                event.datetime = dt.datetime(_dtime.year, _dtime.month,
                                             _dtime.day, _dtime.hour, _dtime.minute, _dtime.second)
        if 'datetime_in' in event.__dict__:
            if event.datetime_in is not None:
                _dtime = event.datetime_in
                event.datetime_in = dt.datetime(_dtime.year, _dtime.month,
                                                _dtime.day, _dtime.hour, _dtime.minute, _dtime.second)
        self.callback(event)


def get_client(host:str = None, port: int = None, user: str = None, password: str = None):
    """Get RabbitMQ client.

    Returns
    -------
    Client
        RabbitMQ client.
    """

    return pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port,
                                                             credentials=pika.PlainCredentials(user,
                                                                                               password)))


class Emit_Events():
    """ Publish MQ for publishing events by topic"""
    def __init__(self, config: dict = None):
        self.config = config
        self._connect_client()

    @log_start_end(log=logger)
    def _connect_client(self):
        self.connection = get_client(host=self.config['host'], port=self.config['port'],
                                     user=self.config['user'], password=self.config['password'])
        self.properties = pika.BasicProperties(content_type='application/json')
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='events', exchange_type='topic')

    def publish_event(self, topic: str, msg:dataclass):
        """ Publish message Event to MQ by topic, all events are dataclass objects define in events.py """
        # past datetime to UTC
        _d = msg.datetime
        if _d.tzinfo is not None: # if not time info, supposse it is UTC
            _d = msg.datetime.astimezone(pytz.utc)
        dtime = dt.datetime(_d.year, _d.month, _d.day,_d.hour, _d.minute, _d.second, 0,pytz.UTC)
        msg.datetime = dtime
        try:
            self.channel.basic_publish(exchange='events', routing_key=topic, properties =self.properties,
                                       body=msg.to_json())
        except Exception as e:
            time.sleep(1)
            self._connect_client() # connect to MQ if connection is lost
            self.channel.basic_publish(exchange='events', routing_key=topic, properties=self.properties,
                                       body=msg.to_json())

    def publish(self, topic: str, message: str):
        """ Publish String  to MQ by topic, this is the generic case"""
        self.channel.basic_publish(exchange='events', routing_key=topic, properties=self.properties,
                                   body=message)

    def close(self):
        """ Close MQ connection """
        self.connection.close()


@log_start_end(log=logger)
def receive_events(routing_key: str = "#", topic: str ='events', callback: callable=None,
                   config: dict = None, block=True):
    """ Receive events from MQ by topic """
    if callback is not None and topic == 'events':
        callBack_handler = CallBack_Handler(callback=callback)
        callback = callBack_handler.callback_recieved
    else:
        callback = _callback
    # Conenect to MQ
    connection = get_client(host=config['host'], port=config['port'],
                            user=config['user'], password=config['password'])
    channel = connection.channel()
    channel.exchange_declare(exchange=topic, exchange_type='topic')
    result = channel.queue_declare('', exclusive=True)
    queue_name = result.method.queue
    for routing in routing_key.split(','):
        channel.queue_bind(exchange=topic, queue=queue_name, routing_key=routing)
    channel.queue_bind(exchange=topic, queue=queue_name, routing_key=routing_key)
    print(' [*] Waiting for events. To exit press CTRL+C')
    channel.basic_consume(
        queue=queue_name, on_message_callback=callback, auto_ack=True)
    if block:
        channel.start_consuming()
    else:
        return connection