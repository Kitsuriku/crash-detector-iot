"""Debug: kirim 1 crash palsu tanpa HP (bukan edge fisik):  python -m scripts.simulate_ed1"""
import json
from datetime import datetime, timezone
import paho.mqtt.publish as publish
from shared import config

payload = {"isCrash": True, "deviceId": "ED1-sim", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "location": {"lat": -7.0051, "lon": 110.4381, "accuracy": 10},
           "speedBefore": 30, "speedAfter": 0, "gPeak": 4.2, "rotationPeak": 310, "simulated": True}
extra = {}
if config.BROKER_USER:
    extra["auth"] = {"username": config.BROKER_USER, "password": config.BROKER_PASS}
if config.BROKER_TLS:
    extra["tls"] = {}
publish.single(config.TOPIC, json.dumps(payload), qos=1, hostname=config.BROKER_HOST, port=config.BROKER_PORT, **extra)
print("Terkirim ke", config.TOPIC)
