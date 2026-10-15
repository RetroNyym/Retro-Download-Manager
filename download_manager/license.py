"""Retro+ Download Manager — lisans sistemi (Free / Pro).

Lisans anahtarı formatı:  RDM-XXXX-XXXX-XXXX-XXXX
Doğrulama: HMAC-SHA256 tabanlı imza (sunucusuz, offline).
Pro bayrakları: playlist toplu indirme, gelişmiş zamanlama,
çoklu cihaz (3), öncelikli güncelleme, rozet gizleme.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import uuid
from pathlib import Path

# ─── Gizli anahtar (derlemede gömülü) ───────────────────────────────────────
# Bu, lisans anahtarlarını imzalamak için kullanılır.
# Üretimde 32+ rastgele bayt olmalı; burada açık kaynak için sabit.
_SECRET = b"retro-plus-download-manager-pro-2026-secret-key-v1"

# Lisans dosyası adı (kullanıcı profili klasöründe saklanır)
LICENSE_FILENAME = ".retro_plus_license.json"

# Pro özellik listesi (UI'da gösterilir)
PRO_FEATURES = (
    ("playlist", "Çalma listesi toplu indirme (YouTube, Spotify, SoundCloud)"),
    ("schedule", "Gelişmiş zamanlama (haftalık, tekrarlayan görevler)"),
    ("multi_device", "3 cihaza kadar lisans"),
    ("priority_update", "Öncelikli güncelleme bildirimi"),
    ("no_badge", "Arayüzde rozet/versiyon etiketi gizleme"),
)


def _b32(data: bytes) -> str:
    """Base32 benzeri, okunabilir encoding (I, L, O, Q hariç)."""
    alphabet = "ABCDEFGHJKMNPRTUVWXYZ23456789"  # 29 karakter
    n = int.from_bytes(data, "big")
    chars = []
    while n > 0:
        n, r = divmod(n, len(alphabet))
        chars.append(alphabet[r])
    return "".join(reversed(chars)) or "2"


def _unb32(text: str) -> bytes:
    alphabet = "ABCDEFGHJKMNPRTUVWXYZ23456789"
    n = 0
    for ch in text.upper():
        idx = alphabet.find(ch)
        if idx < 0:
            raise ValueError(f"Geçersiz karakter: {ch}")
        n = n * len(alphabet) + idx
    # 12 byte'a genişlet (payload 6 + signature 6)
    length = (n.bit_length() + 7) // 8 or 1
    return n.to_bytes(max(length, 12), "big")


def _sign(payload: bytes) -> bytes:
    return hmac.new(_SECRET, payload, hashlib.sha256).digest()[:6]


def generate_key(seats: int = 3, kind: str = "lifetime") -> str:
    """Lisans anahtarı üretir (satış sonrası müşteriye verilir).

    seats: cihaz sayısı (varsayılan 3)
    kind:  'lifetime' | 'year' | 'trial'
    """
    kind_byte = {"lifetime": b"L", "year": b"Y", "trial": b"T"}.get(kind, b"L")
    seats_byte = bytes([min(max(seats, 1), 9)])
    rand = os.urandom(4)
    payload = kind_byte + seats_byte + rand  # 6 byte
    signature = _sign(payload)  # 6 byte
    blob = payload + signature  # 12 byte = 96 bit
    body = _b32(blob)  # ~20 karakter (29^20 ≈ 97 bit)
    # Pad to exactly 20 chars
    body = body.rjust(20, "2")
    groups = [body[i:i + 4] for i in range(0, 20, 4)]
    return "RDM1-" + "-".join(groups)


def parse_key(key: str) -> dict | None:
    """Lisans anahtarını ayrıştırır. Geçersizse None döner."""
    if not key or not isinstance(key, str):
        return None
    key = key.strip().upper()
    m = re.fullmatch(r"RDM1-([A-Z0-9]{4})-([A-Z0-9]{4})-([A-Z0-9]{4})-([A-Z0-9]{4})-([A-Z0-9]{4})", key)
    if not m:
        return None
    body = "".join(m.groups())
    try:
        blob = _unb32(body)
    except ValueError:
        return None
    if len(blob) < 12:
        return None
    payload, signature = blob[:6], blob[6:12]
    if not hmac.compare_digest(_sign(payload), signature):
        return None
    kind = {b"L": "lifetime", b"Y": "year", b"T": "trial"}.get(payload[0:1], "lifetime")
    seats = payload[1]
    return {"kind": kind, "seats": seats, "raw": key}


def is_valid(key: str) -> bool:
    return parse_key(key) is not None


# ─── Lisans dosyası yönetimi ────────────────────────────────────────────────

def _license_path() -> Path:
    return Path.home() / LICENSE_FILENAME


def load_license() -> dict | None:
    """Kayıtlı lisansı yükler (yoksa None)."""
    try:
        data = json.loads(_license_path().read_text(encoding="utf-8"))
        key = data.get("key", "")
        parsed = parse_key(key)
        if parsed:
            parsed["activated_at"] = data.get("activated_at", "")
            parsed["device_id"] = data.get("device_id", "")
            return parsed
    except Exception:
        pass
    return None


def save_license(key: str, device_id: str = "") -> bool:
    """Lisansı dosyaya kaydeder. Başarılıysa True."""
    parsed = parse_key(key)
    if not parsed:
        return False
    from datetime import datetime, timezone
    record = {
        "key": key.strip().upper(),
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "device_id": device_id or _device_fingerprint(),
    }
    try:
        _license_path().write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def clear_license():
    try:
        _license_path().unlink(missing_ok=True)
    except OSError:
        pass


def _device_fingerprint() -> str:
    """Basit cihaz parmak izi (MAC + makine adı hash'i)."""
    raw = f"{uuid.getnode()}-{os.environ.get('COMPUTERNAME', '')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ─── Pro tespiti ────────────────────────────────────────────────────────────

class LicenseManager:
    """Uygulama genelinde Pro durumunu tutar."""

    def __init__(self):
        self._license: dict | None = None
        self.refresh()

    def refresh(self) -> None:
        self._license = load_license()

    @property
    def is_pro(self) -> bool:
        return self._license is not None

    @property
    def info(self) -> dict | None:
        return dict(self._license) if self._license else None

    @property
    def kind(self) -> str:
        return (self._license or {}).get("kind", "free")

    @property
    def seats(self) -> int:
        return int((self._license or {}).get("seats", 0))

    def activate(self, key: str) -> bool:
        if save_license(key):
            self.refresh()
            return True
        return False

    def deactivate(self) -> None:
        clear_license()
        self.refresh()

    def has(self, feature: str) -> bool:
        """Pro özelliğinin kullanılıp kullanılamayacağını döndürür."""
        return self.is_pro


# Modül seviyesinde tekil örnek (gui.py bunu kullanır)
_manager = LicenseManager()


def get_license_manager() -> LicenseManager:
    return _manager


def is_pro() -> bool:
    _manager.refresh()
    return _manager.is_pro


def has_feature(feature: str) -> bool:
    _manager.refresh()
    return _manager.has(feature)
