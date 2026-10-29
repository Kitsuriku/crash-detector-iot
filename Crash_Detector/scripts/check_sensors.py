"""Cek sensor Termux sebelum menjalankan hp_ed1.py:  python -m scripts.check_sensors"""
import subprocess


def run(title, *cmd):
    print(f"\n== {title} ==")
    try:
        subprocess.run(cmd, timeout=60)
    except FileNotFoundError:
        print("Perintah tidak ditemukan: jalankan `pkg install termux-api` dan pasang aplikasi Termux:API")
    except subprocess.TimeoutExpired:
        print("Timeout: periksa izin lokasi/sensor untuk Termux:API")


run("Daftar sensor", "termux-sensor", "-l")
run("Accelerometer + gyroscope (1 sampel)", "termux-sensor", "-s", "accelerometer,gyroscope", "-n", "1")
run("GPS (butuh di luar ruangan)", "termux-location", "-p", "gps", "-r", "once")
