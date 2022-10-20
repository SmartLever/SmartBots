""" Webhook socket and send to MQ broker """
from flask import Flask, request
from smartbots import conf
import datetime as dt
from smartbots.events import WebHook as WebHookEvent
from smartbots.brokerMQ import Emit_Events

# Flask app should start in global layout
app = Flask(__name__)

# keys for filter
keys = [conf.WEBHOOKS[k] for k in conf.WEBHOOKS.keys() if len(conf.WEBHOOKS[k]) > 0]

# Start publishing events in MQ
emit = Emit_Events()

def get_datetime():
    timestamp = dt.datetime.utcnow()
    return timestamp


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        dtime = get_datetime()
        if request.method == "POST":
            data = request.get_json()
            key = data["key"]
            _type = data["type"]
            ticker = data["ticker"]

            if key in keys:
                hook = WebHookEvent(event_type="webhook", hook_type=_type, msg=data,
                                    datetime=dtime, ticker=ticker)
                print("[X]", dtime, "Alert Received")
                print(hook)
                emit.publish_event("webhook", hook)
                return "Sent alert", 200

            else:
                print("[X]", dtime, "Alert Received & Refused! (Wrong Key)")
                return "Refused alert", 400

    except Exception as e:
        print("[X]", dtime, "Error:\n>", e)
        return "Error", 400


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)