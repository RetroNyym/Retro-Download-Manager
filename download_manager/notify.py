"""Bildirim sesleri ve masaustu bilgilendirmeleri."""

from __future__ import annotations

import sys

_PATTERNS = {
    "ok": ((880, 110), (1175, 160), (1568, 200)),
    "error": ((440, 180), (330, 260)),
    "warn": ((660, 140), (550, 200)),
    "info": ((760, 90),),
}


def beep(kind="info"):
    pattern = _PATTERNS.get(kind, _PATTERNS["info"])
    try:
        import winsound
    except Exception:
        for _ in range(1):
            sys.stdout.write("\a")
            sys.stdout.flush()
        return
    for freq, duration in pattern:
        try:
            winsound.Beep(freq, duration)
        except Exception:
            break


def notify(kind="info", enabled=True):
    if enabled:
        beep(kind)
