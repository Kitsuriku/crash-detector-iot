"""Konfigurasi bersama (dibaca dari .env)."""
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID", "crash_kelompok_01")
BROKER_HOST = os.getenv("BROKER_HOST", "broker.hivemq.com")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
BROKER_USER = os.getenv("BROKER_USER") or None
BROKER_PASS = os.getenv("BROKER_PASS") or None
BROKER_TLS = os.getenv("BROKER_TLS", str(BROKER_PORT != 1883)).lower() == "true"  # HiveMQ Cloud: 8883 + TLS
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
TOPIC = f"crashdetector/{PROJECT_ID}/crash"
THRESHOLDS = dict(spd=float(os.getenv("SPEED_BEFORE_KPH", "30")), stop=float(os.getenv("STOP_KPH", "5")),
                  g=float(os.getenv("IMPACT_G", "3")), rot=float(os.getenv("ROTATION_DPS", "250")))


def mqtt_client(name):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"cd_{name}_{os.urandom(3).hex()}")
    if BROKER_USER:
        c.username_pw_set(BROKER_USER, BROKER_PASS)
    if BROKER_TLS:
        c.tls_set()  # memakai sertifikat CA bawaan sistem
    return c
