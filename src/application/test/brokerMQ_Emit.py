""" Test brokerMQ Emit"""
import pika
import sys
from src.application import conf

connection = pika.BlockingConnection(pika.ConnectionParameters(host=conf.RABBITMQ_HOST, port=conf.RABBITMQ_PORT,
                                                               credentials=pika.PlainCredentials(conf.RABBITMQ_USER,
                                                                                                 conf.RABBITMQ_PASSWORD)))
channel = connection.channel()

channel.exchange_declare(exchange='events', exchange_type='topic')


message = ' '.join(sys.argv[2:]) or 'Hello World!'
channel.basic_publish(
    exchange='events', routing_key='test', body=message)
print(" [x] Sent %r:%r" % ('test', message))
connection.close()