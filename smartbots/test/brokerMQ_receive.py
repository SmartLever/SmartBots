import pika
import sys
from smartbots.brokerMQ import receive_events

receive_events('test', callback=None)