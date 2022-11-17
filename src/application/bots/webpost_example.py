""" Example Weebpost and recieved script. """
import requests
import json
import time
from src.infrastructure.brokerMQ import receive_events
import schedule
import threading

def run():
    def send():
        # Send post

        webhook_url = 'http://localhost/webhook'
        data = {"exchange":"exchange","price": 16522 ,"key":"1234ase",
                "type":"strategy","ticker":"BTCUSD",
                 "name":"MA2",
                 "action":"buy" ,
                "contracts":1,
                "interval":"1",
                "position_size":1,
                "market_position":"long",
                "prev_market_position":"short"}

        requests.post(webhook_url, data=json.dumps(data), headers={'Content-Type': 'application/json'})

    # create thead for send post
    schedule.every(10).seconds.do(send)
    while True:
        schedule.run_pending()
        time.sleep(1)


x = threading.Thread(target=run)
x.start()

# receive events from MQ
config = {'host': 'localhost', 'port': 5672, 'user': 'guest', 'password': 'guest'}
receive_events(routing_key='webhook',config=config)




