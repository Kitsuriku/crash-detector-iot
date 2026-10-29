# Menjalankan edge di Android (Termux)

1. Pasang **Termux** dan **Termux:API** dari F-Droid (versi Play Store sudah usang). Beri izin Lokasi dan Sensor untuk Termux:API.
2. Di Termux:
   ```bash
   pkg update && pkg install python git termux-api
   git clone <url-repo-kamu>.git crash-detector-iot && cd crash-detector-iot
   python -m pip install -r requirements.txt
   cp .env.example .env && nano .env      # samakan PROJECT_ID dengan laptop
   termux-wake-lock                       # cegah HP tidur
   ```
3. Cek sensor: `python -m scripts.check_sensors` (GPS butuh di luar ruangan).
4. **HP A:** `python hp_ed1.py`  |  **HP B:** `python hp_ed2.py`
5. Debug data mentah: `python hp_ed1.py --debug-sensors`. Ketik `s` + Enter di HP A untuk simulasi kecelakaan.

Jika nama sensor tidak terbaca, lihat `termux-sensor -l`; `hp_ed1.py` memilih sensor yang namanya mengandung "accel" dan "gyro".
