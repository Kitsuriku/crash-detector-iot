"""NODE 2 (HP B / ED2, Termux): terima kondisi kecelakaan + lokasi dari broker, bunyikan alarm."""
import json
import subprocess
from shared import config


def num(v):  # data dari broker publik tidak tepercaya
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def run(*cmd):
    try:
        subprocess.run(cmd, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # bukan di Termux: cukup cetak ke layar


def on_connect(client, userdata, flags, rc, props=None):
    print(f"ED2 terhubung ({rc}) | topic {config.TOPIC}")
    client.subscribe(config.TOPIC, qos=1)


def on_message(client, userdata, msg):
    try:
        d = json.loads(msg.payload)
    except ValueError:
        return
    if not isinstance(d, dict) or d.get("isCrash") is not True:
        return
    loc = d.get("location") or {}
    lat, lon = num(loc.get("lat")), num(loc.get("lon"))
    maps = f"https://www.google.com/maps?q={lat},{lon}" if lat is not None and lon is not None else "lokasi tidak tersedia"
    info = f"{num(d.get('speedBefore'))} -> {num(d.get('speedAfter'))} km/jam | {num(d.get('gPeak'))} g"
    print(f"\n*** KECELAKAAN TERDETEKSI ***\n{info}\n{maps}")
    run("termux-notification", "--id", "crash", "--title", "KECELAKAAN TERDETEKSI",
        "--content", f"{info}. {maps}", "--priority", "max", "--vibrate", "500,200,500,200,500")
    run("termux-vibrate", "-d", "1500", "-f")
    run("termux-tts-speak", "Kecelakaan terdeteksi")


client = config.mqtt_client("ed2")
client.on_connect, client.on_message = on_connect, on_message
client.connect_async(config.BROKER_HOST, config.BROKER_PORT)
client.loop_forever()
