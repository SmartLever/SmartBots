""" Example Weebpost and recieved script. """
import requests
import json
import time
from smartbots.brokerMQ import receive_events
import schedule
import threading

def run():
    def send():
        # Send post

        webhook_url = 'http://140.238.85.81:80/webhook'
        data = {'name': 'This is an example for webhook', "key": "1234ase",
                'type': 'indicator', 'ticker': 'indicator1'}

        requests.post(webhook_url, data=json.dumps(data), headers={'Content-Type': 'application/json'})

    # create thead for send post
    schedule.every(10).seconds.do(send)
    while True:
        schedule.run_pending()
        time.sleep(1)


x = threading.Thread(target=run)
x.start()

# receive events from MQ
receive_events(routing_key='webhook')




