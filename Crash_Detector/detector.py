"""NODE 3 (laptop): subscribe broker, catat crash ke CSV, dan sajikan dashboard di http://localhost:8000."""
import csv
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from shared import config

ROOT = Path(__file__).parent
LOG = ROOT / "crash_log.csv"
STATE = {"connected": False, "alarm": False, "events": []}
LOCK = threading.Lock()


def num(v):  # data dari broker publik tidak tepercaya
    try:
        return round(float(v), 5)
    except (TypeError, ValueError):
        return None


def on_connect(client, userdata, flags, rc, props=None):
    STATE["connected"] = not rc.is_failure
    client.subscribe(config.TOPIC, qos=1)
    print(f"Broker {config.BROKER_HOST}:{config.BROKER_PORT} ({rc}), subscribe {config.TOPIC}")


def on_disconnect(client, userdata, flags, rc, props=None):
    STATE["connected"] = False


def on_message(client, userdata, msg):
    try:
        d = json.loads(msg.payload)
    except ValueError:
        return
    if not isinstance(d, dict) or d.get("isCrash") is not True:
        return
    loc = d.get("location") or {}
    ev = {"ts": str(d.get("ts"))[:40], "lat": num(loc.get("lat")), "lon": num(loc.get("lon")),
          "speedBefore": num(d.get("speedBefore")), "speedAfter": num(d.get("speedAfter")),
          "gPeak": num(d.get("gPeak")), "rotationPeak": num(d.get("rotationPeak")),
          "simulated": d.get("simulated") is True}
    with LOCK:
        STATE["events"].insert(0, ev)
        del STATE["events"][50:]
        STATE["alarm"] = True
    new = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ev))
        if new:
            w.writeheader()
        w.writerow(ev)
    print(f"[CRASH] {ev}")


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self.send(200, (ROOT / "dashboard" / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/state":
            with LOCK:
                self.send(200, {**STATE, "project": config.PROJECT_ID, "topic": config.TOPIC, "broker": config.BROKER_HOST})
        else:
            self.send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/reset":
            STATE["alarm"] = False
            self.send(200, {"ok": True})
        else:
            self.send(404, {"error": "not found"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    client = config.mqtt_client("detector")
    client.on_connect, client.on_disconnect, client.on_message = on_connect, on_disconnect, on_message
    client.connect_async(config.BROKER_HOST, config.BROKER_PORT)
    client.loop_start()
    print(f"Dashboard: http://localhost:{config.DASHBOARD_PORT}  (Ctrl+C untuk berhenti)")
    ThreadingHTTPServer(("127.0.0.1", config.DASHBOARD_PORT), Handler).serve_forever()
