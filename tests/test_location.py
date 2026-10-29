import unittest
from shared.location import LocationSharer

LAT, LON = -7.0, 110.0
M10 = 0.0001  # ~11 m dalam derajat lintang


class TestLocationSharer(unittest.TestCase):
    def test_fix_pertama_langsung_dikirim(self):
        p = LocationSharer().update(LAT, LON, 5, 0, now=1000)
        self.assertEqual(p["location"], {"lat": LAT, "lon": LON, "accuracy": 5})
        self.assertEqual(p["seq"], 1)

    def test_jeda_minimal_walau_bergerak(self):
        s = LocationSharer(interval=5)
        s.update(LAT, LON, 5, now=1000)
        self.assertIsNone(s.update(LAT + 5 * M10, LON, 5, now=1002))   # terlalu cepat
        self.assertIsNotNone(s.update(LAT + 5 * M10, LON, 5, now=1006))

    def test_diam_tidak_dikirim_sebelum_heartbeat(self):
        s = LocationSharer(interval=5, heartbeat=30)
        s.update(LAT, LON, 5, now=1000)
        self.assertIsNone(s.update(LAT, LON, 5, now=1010))              # diam, belum 30 dtk
        self.assertIsNotNone(s.update(LAT, LON, 5, now=1031))           # heartbeat

    def test_bergeser_cukup_jauh_dikirim(self):
        s = LocationSharer(interval=5, min_move=10)
        s.update(LAT, LON, 5, now=1000)
        self.assertIsNone(s.update(LAT + 0.00003, LON, 5, now=1006))    # ~3 m
        self.assertIsNotNone(s.update(LAT + M10, LON, 5, now=1012))     # ~11 m

    def test_akurasi_buruk_diabaikan(self):
        s = LocationSharer(max_acc=100)
        self.assertIsNone(s.update(LAT, LON, 500, now=1000))
        self.assertIsNotNone(s.update(LAT, LON, None, now=1001))        # akurasi tak diketahui tetap diterima


if __name__ == "__main__":
    unittest.main()
