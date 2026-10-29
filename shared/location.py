"""Algoritma GPS ED1 -> ED2: kapan posisi terbaru dikirim ke broker."""
import time
from datetime import datetime, timezone
from .detection import haversine


class LocationSharer:
    """Kirim posisi hanya bila perlu (hemat baterai dan kuota):
    - jeda minimal `interval` detik antar kiriman,
    - kirim bila sudah bergeser >= `min_move` meter,
    - tetap kirim tiap `heartbeat` detik walau diam (tanda ED1 masih hidup),
    - abaikan fix GPS yang akurasinya lebih buruk dari `max_acc` meter."""

    def __init__(self, interval=5, min_move=10, heartbeat=30, max_acc=100, device_id="ED1"):
        self.interval, self.min_move, self.heartbeat, self.max_acc = interval, min_move, heartbeat, max_acc
        self.device_id = device_id
        self.last = None  # (lat, lon, waktu kirim terakhir)
        self.seq = 0

    def update(self, lat, lon, acc=None, speed_kph=0.0, now=None):
        """Panggil tiap ada fix GPS baru. Mengembalikan payload bila harus dikirim, selain itu None."""
        now = time.time() if now is None else now
        if acc is not None and acc > self.max_acc:
            return None
        if self.last:
            elapsed = now - self.last[2]
            if elapsed < self.interval:
                return None
            if elapsed < self.heartbeat and haversine(self.last[0], self.last[1], lat, lon) < self.min_move:
                return None
        self.last = (lat, lon, now)
        self.seq += 1
        return {"deviceId": self.device_id, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "seq": self.seq, "location": {"lat": lat, "lon": lon, "accuracy": acc},
                "speedKph": round(speed_kph or 0, 1)}
