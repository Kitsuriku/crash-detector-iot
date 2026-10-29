import unittest
from shared.detection import CrashDetector


def run(impact):
    d, t = CrashDetector(), 1000.0
    for i in range(4):
        d.on_gps(-7, 110, 5, 35 / 3.6, now=t + i)       # 35 km/jam
    if impact:
        d.on_accel(0, 0, 5 * 9.81, now=t + 3.5)         # benturan 5 g
    d.on_gps(-7, 110, 5, 0, now=t + 4)                  # berhenti
    return d.check(now=t + 4)


class TestDetection(unittest.TestCase):
    def test_crash_dengan_benturan(self):
        p = run(True)
        self.assertTrue(p["isCrash"])
        self.assertGreaterEqual(p["speedBefore"], 30)

    def test_rem_mendadak_tanpa_benturan_bukan_crash(self):
        self.assertIsNone(run(False))

    def test_cooldown(self):
        d = CrashDetector()
        self.assertTrue(d.check(now=1000, force=True)["isCrash"])
        self.assertIsNone(d.check(now=1010))


if __name__ == "__main__":
    unittest.main()
