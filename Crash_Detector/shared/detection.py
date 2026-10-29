"""Pengolahan data ED1: fusi GPS (kecepatan) + accelerometer (benturan) + gyroscope (rotasi)."""
import math
import time
from collections import deque
from datetime import datetime, timezone


def haversine(lat1, lon1, lat2, lon2):
    r, p = 6371000, math.radians
    h = math.sin(p(lat2 - lat1) / 2) ** 2 + math.cos(p(lat1)) * math.cos(p(lat2)) * math.sin(p(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


class CrashDetector:
    def __init__(self, spd=30, stop=5, g=3, rot=250, cooldown=30):
        self.spd, self.stop, self.g, self.rot, self.cooldown = spd, stop, g, rot, cooldown
        self.hist = deque()          # (waktu, km/jam) 5 detik terakhir
        self.speed = self.g_now = self.rot_now = 0.0
        self.pos = self.prev = None
        self.last_imp = self.last_rot = self.last_crash = -1e9
        self.g_peak = self.rot_peak = 0.0

    def on_gps(self, lat, lon, acc, speed_ms=None, now=None):
        now = now or time.time()
        if speed_ms is None and self.prev:  # cadangan: jarak antar titik / waktu
            speed_ms = haversine(self.prev[0], self.prev[1], lat, lon) / max(now - self.prev[2], 0.5)
        self.prev, self.pos = (lat, lon, now), {"lat": lat, "lon": lon, "accuracy": acc}
        self.speed = (speed_ms or 0) * 3.6
        self.hist.append((now, self.speed))

    def on_accel(self, x, y, z, now=None):  # m/s^2 termasuk gravitasi
        now = now or time.time()
        self.g_now = math.sqrt(x * x + y * y + z * z) / 9.81
        if self.g_now >= self.g:
            self.last_imp, self.g_peak = now, max(self.g_peak, self.g_now)

    def on_gyro(self, x, y, z, now=None):  # rad/s (satuan Android)
        now = now or time.time()
        self.rot_now = math.degrees(math.sqrt(x * x + y * y + z * z))
        if self.rot_now >= self.rot:
            self.last_rot, self.rot_peak = now, max(self.rot_peak, self.rot_now)

    def check(self, now=None, force=False, simulated=False):
        """Crash = kecepatan turun mendadak (mis. 30 -> 0 km/jam) DAN ada benturan/rotasi keras."""
        now = now or time.time()
        while self.hist and now - self.hist[0][0] > 5:
            self.hist.popleft()
        if not force and now - self.last_crash < self.cooldown:
            return None
        before = max([v for _, v in self.hist], default=0.0)
        stopped = before >= self.spd and self.speed <= self.stop
        hit = now - self.last_imp < 4 or now - self.last_rot < 4
        if not (force or (stopped and hit)):
            return None
        self.last_crash = now
        payload = {"isCrash": True, "deviceId": "ED1", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "location": self.pos, "speedBefore": 30 if simulated else round(before, 1),
                   "speedAfter": 0 if simulated else round(self.speed, 1),
                   "gPeak": round(self.g_peak, 2), "rotationPeak": round(self.rot_peak), "simulated": simulated}
        self.g_peak = self.rot_peak = 0.0
        return payload
