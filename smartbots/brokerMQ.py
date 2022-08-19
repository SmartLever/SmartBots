""" Wrappe around MQ broker, using Rabbitmq
LocalHost: http://localhost:15672/
"""
import time

import pika
from smartbots import conf
import json
import logging
from smartbots.decorators import log_start_end, check_api_key
from smartbots.events import Bar, Order
from dataclasses import dataclass
import datetime as dt
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

events_type = {'bar': Bar, 'order': Order,'order_status': Order} #define types of events


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
        event = events_type[method.routing_key].from_json(body)
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
        self.callback({method.routing_key: event})


@check_api_key(
     [
         "RABBITMQ_HOST",
         "RABBITMQ_PORT",
         "RABBITMQ_USER",
         "RABBITMQ_PASSWORD"
     ]
 )
def get_client():
    """Get RabbitMQ client.

    Returns
    -------
    Client
        RabbitMQ client.
    """

    return pika.BlockingConnection(pika.ConnectionParameters(host=conf.RABBITMQ_HOST, port=conf.RABBITMQ_PORT,
                                                             credentials=pika.PlainCredentials(conf.RABBITMQ_USER,
                                                             conf.RABBITMQ_PASSWORD)))


class Emit_Events():
    """ Publish MQ for publishing events by topic"""
    def __init__(self):
        self._connect_client()

    @log_start_end(log=logger)
    def _connect_client(self):
        self.connection = get_client()
        self.properties = pika.BasicProperties(content_type='application/json')
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='events', exchange_type='topic')


    def publish_event(self, topic: str, message:dataclass):
        """ Publish message Event to MQ by topic, all events are dataclass objects define in events.py """
        try:
            self.channel.basic_publish(exchange='events', routing_key=topic,properties =self.properties,
                                       body=message.to_json())
        except Exception as e:
            time.sleep(1)
            self._connect_client() # connect to MQ if connection is lost
            self.channel.basic_publish(exchange='events', routing_key=topic, properties=self.properties,
                                       body=message.to_json())

    def publish(self, topic: str, message: str):
        """ Publish String  to MQ by topic, this is the generic case"""
        self.channel.basic_publish(exchange='events', routing_key=topic, properties=self.properties,
                                   body=message)

    def close(self):
        """ Close MQ connection """
        self.connection.close()


@log_start_end(log=logger)
def receive_events(routing_key: str = "#", topic: str ='events', callback: callable=None):
    """ Receive events from MQ by topic """
    if callback is not None and topic == 'events':
        callBack_handler = CallBack_Handler(callback=callback)
        callback = callBack_handler.callback_recieved
    else:
        callback = _callback
    # Conenect to MQ
    connection = get_client()
    channel = connection.channel()
    channel.exchange_declare(exchange=topic, exchange_type='topic')
    result = channel.queue_declare('', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=topic, queue=queue_name, routing_key=routing_key)
    print(' [*] Waiting for events. To exit press CTRL+C')
    channel.basic_consume(
        queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


if __name__ == '__main__':
   receive_events(routing_key='order')