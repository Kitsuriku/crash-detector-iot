"""NODE 2 (HP B / ED2, Termux): terima lokasi live ED1 + kondisi kecelakaan dari broker, bunyikan alarm."""
import json
import subprocess
import time
from shared import config

LAST = {"fix": None, "at": 0.0}  # lokasi live terakhir dari ED1: (lat, lon, akurasi)


def num(v):  # data dari broker publik tidak tepercaya
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_loc(loc):
    """Ambil (lat, lon, akurasi) dari dict lokasi; None bila tidak valid (NaN/di luar jangkauan juga ditolak)."""
    loc = loc if isinstance(loc, dict) else {}
    lat, lon = num(loc.get("lat")), num(loc.get("lon"))
    if lat is None or lon is None or not (abs(lat) <= 90 and abs(lon) <= 180):
        return None
    return lat, lon, num(loc.get("accuracy"))


def run(*cmd):
    try:
        subprocess.run(cmd, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # bukan di Termux: cukup cetak ke layar


def on_connect(client, userdata, flags, rc, props=None):
    print(f"ED2 terhubung ({rc}) | topic {config.TOPIC} + {config.LOCATION_TOPIC}")
    client.subscribe([(config.TOPIC, 1), (config.LOCATION_TOPIC, 0)])


def on_location(d):
    fix = parse_loc(d.get("location"))
    if not fix:
        return
    LAST["fix"], LAST["at"] = fix, time.time()
    acc = f" (±{fix[2]:.0f} m)" if fix[2] is not None else ""
    print(f"\rED1 live: {fix[0]:.5f}, {fix[1]:.5f}{acc} | {time.strftime('%H:%M:%S')}   ", end="", flush=True)


def on_crash(d):
    fix, note = parse_loc(d.get("location")), ""
    if fix is None and LAST["fix"]:  # GPS ED1 hilang saat benturan -> pakai lokasi live terakhir
        fix, note = LAST["fix"], f" (lokasi terakhir, {int(time.time() - LAST['at'])} dtk lalu)"
    maps = f"https://www.google.com/maps?q={fix[0]},{fix[1]}{note}" if fix else "lokasi tidak tersedia"
    info = f"{num(d.get('speedBefore'))} -> {num(d.get('speedAfter'))} km/jam | {num(d.get('gPeak'))} g"
    print(f"\n*** KECELAKAAN TERDETEKSI ***\n{info}\n{maps}")
    run("termux-notification", "--id", "crash", "--title", "KECELAKAAN TERDETEKSI",
        "--content", f"{info}. {maps}", "--priority", "max", "--vibrate", "500,200,500,200,500")
    run("termux-vibrate", "-d", "1500", "-f")
    run("termux-tts-speak", "Kecelakaan terdeteksi")


def on_message(client, userdata, msg):
    try:
        d = json.loads(msg.payload)
    except ValueError:
        return
    if not isinstance(d, dict):
        return
    if msg.topic == config.LOCATION_TOPIC:
        on_location(d)
    elif d.get("isCrash") is True:
        on_crash(d)


if __name__ == "__main__":
    client = config.mqtt_client("ed2")
    client.on_connect, client.on_message = on_connect, on_message
    client.connect_async(config.BROKER_HOST, config.BROKER_PORT)
    client.loop_forever()
