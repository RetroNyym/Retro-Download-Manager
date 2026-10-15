"""Retro+ Download Manager — lisans sistemi (Free / Pro).

Lisans anahtarı formatı:  RDM1-XXXX-XXXX-XXXX-XXXX
Doğrulama: HMAC-SHA256 tabanlı imza (sunucusuz, offline).

Türler (kind):
  trial      → 5 indirme hakkı (deneme)
  halfyear   → 6 aylık lisans
  year       → 1 yıllık lisans
  lifetime   → ömür boyu lisans

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
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ─── Gizli anahtar (derlemede gömülü) ───────────────────────────────────────
# Bu, lisans anahtarlarını imzalamak için kullanılır.
# Üretimde 32+ rastgele bayt olmalı; burada açık kaynak için sabit.
_SECRET = b"retro-plus-download-manager-pro-2026-secret-key-v1"

# Lisans dosyası adı (kullanıcı profili klasöründe saklanır)
LICENSE_FILENAME = ".retro_plus_license.json"

# Tür → kod eşlemesi
KIND_CODES = {
    "trial": b"T",
    "halfyear": b"H",
    "year": b"Y",
    "lifetime": b"L",
}
CODE_KINDS = {v: k for k, v in KIND_CODES.items()}

# Tür → süre (gün); None = süresiz
KIND_DURATIONS = {
    "trial": None,       # indirme sayacı ile sınırlı
    "halfyear": 183,     # 6 ay
    "year": 365,
    "lifetime": None,
}

# Trial indirme hakkı
TRIAL_DOWNLOADS = 5

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
    kind:  'lifetime' | 'halfyear' | 'year' | 'trial'
    """
    kind_byte = KIND_CODES.get(kind, b"L")
    seats_byte = bytes([min(max(seats, 1), 9)])
    rand = os.urandom(4)
    payload = kind_byte + seats_byte + rand  # 6 byte
    signature = _sign(payload)  # 6 byte
    blob = payload + signature  # 12 byte = 96 bit
    body = _b32(blob)  # ~20 karakter (29^20 ≈ 97 bit)
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
    kind = CODE_KINDS.get(payload[0:1], "lifetime")
    seats = payload[1]
    return {"kind": kind, "seats": seats, "raw": key}


def is_valid(key: str) -> bool:
    return parse_key(key) is not None


# ─── Lisans dosyası yönetimi ────────────────────────────────────────────────

def _license_path() -> Path:
    return Path.home() / LICENSE_FILENAME


def load_license() -> dict | None:
    """Kayıtlı lisansı yükler (süre dolmuşsa/indirme bittiyse None)."""
    try:
        data = json.loads(_license_path().read_text(encoding="utf-8"))
        key = data.get("key", "")
        parsed = parse_key(key)
        if not parsed:
            return None
        parsed["activated_at"] = data.get("activated_at", "")
        parsed["device_id"] = data.get("device_id", "")
        parsed["downloads_left"] = data.get("downloads_left")

        # Süre sonu kontrolü (halfyear / year)
        duration = KIND_DURATIONS.get(parsed["kind"])
        if duration is not None and parsed["activated_at"]:
            try:
                start = datetime.fromisoformat(parsed["activated_at"])
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                expiry = start + timedelta(days=duration)
                if datetime.now(timezone.utc) > expiry:
                    return None  # süre doldu
                parsed["expires_at"] = expiry.isoformat()
            except (ValueError, TypeError):
                pass

        # Trial indirme hakkı kontrolü
        if parsed["kind"] == "trial":
            left = parsed.get("downloads_left")
            if left is None:
                left = TRIAL_DOWNLOADS
            if left <= 0:
                return None  # haklar bitti
            parsed["downloads_left"] = left

        return parsed
    except Exception:
        pass
    return None


def save_license(key: str, device_id: str = "") -> bool:
    """Lisansı dosyaya kaydeder. Başarılıysa True."""
    parsed = parse_key(key)
    if not parsed:
        return False
    record = {
        "key": key.strip().upper(),
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "device_id": device_id or _device_fingerprint(),
    }
    if parsed["kind"] == "trial":
        record["downloads_left"] = TRIAL_DOWNLOADS
    try:
        _license_path().write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def consume_download() -> bool:
    """Trial indirme hakkı düşer. Süresiz türlerde True döner.

    Dönüş: True → indirmeye izin var; False → hak bitti.
    """
    try:
        data = json.loads(_license_path().read_text(encoding="utf-8"))
    except Exception:
        return False
    key = data.get("key", "")
    parsed = parse_key(key)
    if not parsed:
        return False
    if parsed["kind"] != "trial":
        return True  # halfyear/year/lifetime sınırsız
    left = int(data.get("downloads_left", TRIAL_DOWNLOADS))
    if left <= 0:
        return False
    data["downloads_left"] = left - 1
    try:
        _license_path().write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def remaining_downloads() -> int | None:
    """Trial kalan indirme hakkı; süresiz türlerde None."""
    try:
        data = json.loads(_license_path().read_text(encoding="utf-8"))
    except Exception:
        return None
    parsed = parse_key(data.get("key", ""))
    if not parsed or parsed["kind"] != "trial":
        return None
    return int(data.get("downloads_left", TRIAL_DOWNLOADS))


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

    @property
    def expires_at(self) -> str:
        return (self._license or {}).get("expires_at", "")

    @property
    def downloads_left(self) -> int | None:
        """Trial kalan hak; süresiz türlerde None."""
        if not self._license:
            return None
        return self._license.get("downloads_left")

    def activate(self, key: str) -> bool:
        if save_license(key):
            self.refresh()
            return True
        return False

    def deactivate(self) -> None:
        clear_license()
        self.refresh()

    def consume_download(self) -> bool:
        """Yeni bir indirme başlarken çağrılır; hak bittiyse False."""
        ok = consume_download()
        self.refresh()
        return ok

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


# ─── Satış defteri (sales paneli için) ──────────────────────────────────────
# Üretilen anahtarlar: sales/keys.json (git'e eklenmez, .gitignore'da)

REGISTRY_DIR = Path(__file__).resolve().parent.parent / "sales"
REGISTRY_FILE = REGISTRY_DIR / "keys.json"


def _load_registry() -> list[dict]:
    try:
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_registry(records: list[dict]) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def issue_key(kind: str = "lifetime", seats: int = 3,
              customer: str = "", note: str = "") -> dict | None:
    """Yeni anahtar üretir ve satış defterine kaydeder."""
    if kind not in KIND_CODES:
        return None
    key = generate_key(seats, kind)
    record = {
        "key": key,
        "kind": kind,
        "seats": seats,
        "customer": customer,
        "note": note,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "status": "issued",
    }
    records = _load_registry()
    records.append(record)
    _save_registry(records)
    return record


def list_keys() -> list[dict]:
    """Satış defterindeki tüm anahtarları döndürür (en yeni üstte)."""
    records = _load_registry()
    return list(reversed(records))


def revoke_key(key: str) -> bool:
    """Anahtarı iptal eder."""
    records = _load_registry()
    for rec in records:
        if rec.get("key", "").upper() == key.upper():
            rec["status"] = "revoked"
            _save_registry(records)
            return True
    return False


def registry_stats() -> dict:
    """Satış istatistikleri."""
    records = _load_registry()
    stats = {"total": len(records), "issued": 0, "revoked": 0}
    by_kind: dict[str, int] = {}
    for rec in records:
        if rec.get("status") == "revoked":
            stats["revoked"] += 1
        else:
            stats["issued"] += 1
            k = rec.get("kind", "?")
            by_kind[k] = by_kind.get(k, 0) + 1
    stats["by_kind"] = by_kind
    return stats
