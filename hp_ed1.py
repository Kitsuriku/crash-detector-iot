"""NODE 1 (HP A / ED1, Termux): baca accelerometer + gyroscope + GPS, kirim crash ke broker."""
import argparse
import json
import sys
import threading
import time
from shared import config, termux
from shared.detection import CrashDetector
from shared.location import LocationSharer

ap = argparse.ArgumentParser()
ap.add_argument("--debug-sensors", action="store_true", help="cetak data sensor mentah")
args = ap.parse_args()

det, lock = CrashDetector(**config.THRESHOLDS), threading.Lock()
sharer = LocationSharer(**config.LOCATION)
client = config.mqtt_client("ed1")
client.connect_async(config.BROKER_HOST, config.BROKER_PORT)
client.loop_start()


def send(payload):
    client.publish(config.TOPIC, json.dumps(payload), qos=1)
    print(f"\n[CRASH] terkirim ke {config.TOPIC}: {payload}")


def send_location(payload):  # QoS 0: lokasi live cukup "kirim lalu lupakan", fix berikutnya menyusul
    client.publish(config.LOCATION_TOPIC, json.dumps(payload), qos=0)


def gps_loop():
    for d in termux.stream(["termux-location", "-p", "gps", "-r", "updates"]):
        if args.debug_sensors:
            print("GPS", d)
        with lock:
            det.on_gps(d["latitude"], d["longitude"], d.get("accuracy"), d.get("speed"))
            fix = sharer.update(d["latitude"], d["longitude"], d.get("accuracy"), det.speed)
        if fix:
            send_location(fix)


def keyboard_loop():  # ketik "s" + Enter = simulasi kecelakaan
    for line in sys.stdin:
        if line.strip().lower() == "s":
            with lock:
                send(det.check(force=True, simulated=True))


threading.Thread(target=gps_loop, daemon=True).start()
threading.Thread(target=keyboard_loop, daemon=True).start()
print(f"ED1 aktif | broker {config.BROKER_HOST} | topic {config.TOPIC} + {config.LOCATION_TOPIC} | ketik 's' untuk simulasi")

last = 0
for d in termux.stream(["termux-sensor", "-s", "accelerometer,gyroscope", "-d", "50"]):
    if args.debug_sensors:
        print("SENSOR", d)
    with lock:
        for name, v in d.items():
            n, vals = name.lower(), v.get("values", [])
            if len(vals) < 3 or "uncal" in n or "linear" in n:
                continue
            if "accel" in n:
                det.on_accel(*vals[:3])
            elif "gyro" in n:
                det.on_gyro(*vals[:3])
        payload = det.check()
        if payload:
            send(payload)
        if time.time() - last > 1:
            last = time.time()
            print(f"\r{det.speed:5.1f} km/jam | {det.g_now:4.1f} g | {det.rot_now:4.0f} deg/s ", end="", flush=True)
