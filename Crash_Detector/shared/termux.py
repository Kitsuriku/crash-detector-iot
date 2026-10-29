"""Baca keluaran JSON berkelanjutan dari perintah Termux:API (termux-sensor, termux-location)."""
import json
import subprocess


def stream(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    buf, depth = "", 0
    try:
        for line in p.stdout:
            buf += line
            depth += line.count("{") - line.count("}")
            if depth <= 0 and buf.strip():
                try:
                    yield json.loads(buf)
                except ValueError:
                    pass
                buf, depth = "", 0
    finally:
        p.terminate()
