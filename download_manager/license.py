"""Retro+ — Lisans sistemi (çoklu ürün, Free / Pro).

Lisans anahtarı formatı:  {PREFIX}-XXXX-XXXX-XXXX-XXXX
  PREFIX = ürün ön eki (RDM1, RVE1, ...)
Doğrulama: HMAC-SHA256 tabanlı imza (sunucusuz, offline).

Payload (6 bayt): product(1) + kind(1) + seats(1) + rand(3)

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
_SECRET = b"retro-plus-download-manager-pro-2026-secret-key-v1"

# Lisans dosyası adı (kullanıcı profili klasöründe saklanır)
LICENSE_FILENAME = ".retro_plus_license.json"

# ─── Ürün tanımları (satış paneli products.json ile genişletilebilir) ───────
# code → (ön ek, ad)
DEFAULT_PRODUCTS: dict[int, dict] = {
    1: {"prefix": "RDM1", "name": "Retro+ Download Manager"},
    2: {"prefix": "RVE1", "name": "Retro+ Video Editor"},
    3: {"prefix": "RMA1", "name": "Retro+ Music Audio"},
    4: {"prefix": "RFC1", "name": "Retro+ File Converter"},
}

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
    "trial": None,
    "halfyear": 183,
    "year": 365,
    "lifetime": None,
}

KIND_LABELS_TR = {
    "trial": "Deneme",
    "halfyear": "6 Aylık",
    "year": "1 Yıllık",
    "lifetime": "Ömür Boyu",
}

# Trial indirme hakkı
TRIAL_DOWNLOADS = 5

# Pro özellik listesi (UI'da gösterilir)
PRO_FEATURES = (
    ("playlist", "Çalma listesi toplu indirme (YouTube, Spotify, SoundCloud)"),
    ("schedule", "Gelişmiş zamanlama (haftalık, tekrarlayan görevler)"),
    ("multi_device", "Çoklu cihaz lisansı"),
    ("priority_update", "Öncelikli güncelleme bildirimi"),
    ("no_badge", "Arayüzde rozet/versiyon etiketi gizleme"),
)


def load_products() -> dict[int, dict]:
    """Ürün listesini yükler (products.json varsa onu, yoksa DEFAULT_PRODUCTS)."""
    path = Path(__file__).resolve().parent.parent / "sales" / "products.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        products = {}
        for item in data:
            code = int(item["code"])
            products[code] = {
                "prefix": item["prefix"].upper(),
                "name": item["name"],
                "prices": item.get("prices", {}),
            }
        if products:
            return products
    except Exception:
        pass
    return dict(DEFAULT_PRODUCTS)


def product_by_code(code: int) -> dict | None:
    return load_products().get(code)


def product_by_prefix(prefix: str) -> tuple[int, dict] | None:
    prefix = prefix.upper()
    for code, info in load_products().items():
        if info["prefix"] == prefix:
            return code, info
    return None


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


def generate_key(seats: int = 3, kind: str = "lifetime",
                 product_code: int = 1) -> str:
    """Lisans anahtarı üretir.

    seats:       cihaz sayısı (1-9)
    kind:        'lifetime' | 'halfyear' | 'year' | 'trial'
    product_code: ürün kodu (1=RDM, 2=RVE, ...)
    """
    kind_byte = KIND_CODES.get(kind, b"L")
    seats_byte = bytes([min(max(seats, 1), 9)])
    product_byte = bytes([min(max(product_code, 1), 255)])
    rand = os.urandom(3)
    payload = product_byte + kind_byte + seats_byte + rand  # 6 byte
    signature = _sign(payload)  # 6 byte
    blob = payload + signature  # 12 byte
    body = _b32(blob).rjust(20, "A")  # "A" = alfabe[0] = 0
    groups = [body[i:i + 4] for i in range(0, 20, 4)]
    prefix = (product_by_code(product_code) or DEFAULT_PRODUCTS[1])["prefix"]
    return f"{prefix}-" + "-".join(groups)


def parse_key(key: str) -> dict | None:
    """Lisans anahtarını ayrıştırır. Geçersizse None döner."""
    if not key or not isinstance(key, str):
        return None
    key = key.strip().upper()
    m = re.fullmatch(
        r"([A-Z0-9]{4})-([A-Z0-9]{4})-([A-Z0-9]{4})-([A-Z0-9]{4})-([A-Z0-9]{4})-([A-Z0-9]{4})",
        key)
    if not m:
        return None
    prefix = m.group(1)
    body = "".join(m.groups()[1:])  # ilk grup prefix, kalan 5 grup veri (20 char)
    try:
        blob = _unb32(body)
    except ValueError:
        return None
    if len(blob) < 12:
        return None
    payload, signature = blob[:6], blob[6:12]
    if not hmac.compare_digest(_sign(payload), signature):
        return None
    product_code = payload[0]
    kind = CODE_KINDS.get(payload[1:2], "lifetime")
    seats = payload[2]
    product = product_by_code(product_code)
    return {
        "kind": kind,
        "seats": seats,
        "raw": key,
        "product_code": product_code,
        "product_prefix": prefix,
        "product_name": (product or {}).get("name", f"Ürün {product_code}"),
    }


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
              customer: str = "", note: str = "",
              product_code: int = 1) -> dict | None:
    """Yeni anahtar üretir ve satış defterine kaydeder."""
    if kind not in KIND_CODES:
        return None
    key = generate_key(seats, kind, product_code)
    product = product_by_code(product_code) or {}
    record = {
        "key": key,
        "product_code": product_code,
        "product": product.get("name", f"Ürün {product_code}"),
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
    """Satış istatistikleri (ürüne göre)."""
    records = _load_registry()
    stats = {"total": len(records), "issued": 0, "revoked": 0,
             "by_kind": {}, "by_product": {}}
    for rec in records:
        if rec.get("status") == "revoked":
            stats["revoked"] += 1
        else:
            stats["issued"] += 1
            k = rec.get("kind", "?")
            stats["by_kind"][k] = stats["by_kind"].get(k, 0) + 1
            p = rec.get("product", "?")
            stats["by_product"][p] = stats["by_product"].get(p, 0) + 1
    return stats
