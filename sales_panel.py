"""Retro+ Pro — Satış Paneli (yerel web arayüzü).

Çalıştırma:
    python sales_panel.py
    → tarayıcıda http://127.0.0.1:8377 açılır

İşlevler:
  • Yeni lisans anahtarı üretme (trial / halfyear / year / lifetime)
  • Anahtar listesi (tür, müşteri, tarih, durum)
  • İptal etme
  • CSV dışa aktarma
  • İstatistikler

Güvenlik: sadece 127.0.0.1 (yerel makine) dinlenir.
"""

from __future__ import annotations

import csv
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from download_manager.license import (  # noqa: E402
    issue_key, list_keys, revoke_key, registry_stats, KIND_CODES,
    TRIAL_DOWNLOADS,
)

HOST = "127.0.0.1"
PORT = 8377

KIND_LABELS = {
    "trial": f"Deneme ({TRIAL_DOWNLOADS} indirme)",
    "halfyear": "6 Aylık",
    "year": "1 Yıllık",
    "lifetime": "Ömür Boyu",
}

PRICING = {
    "trial": "Ücretsiz",
    "halfyear": "₺79",
    "year": "₺119",
    "lifetime": "₺149",
}


def _page(title: str, body: str) -> bytes:
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Retro+ Satış Paneli</title>
<style>
:root {{
  --bg:#0f1115; --surface:#161920; --surface2:#1c2028; --line:#2b3140;
  --text:#e8ebf0; --text2:#9aa3b2; --primary:#6c7bff; --accent:#3ec6e0;
  --success:#3ddc84; --danger:#ff5c72; --warn:#ffb020;
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:var(--bg); color:var(--text); font-family:'Segoe UI',system-ui,sans-serif; font-size:14px; }}
header {{ background:var(--surface); border-bottom:1px solid var(--line); padding:16px 24px; display:flex; justify-content:space-between; align-items:center; }}
header h1 {{ font-size:18px; }}
header .badge {{ background:var(--primary); color:#fff; font-size:11px; padding:3px 8px; border-radius:10px; font-weight:600; }}
.wrap {{ max-width:1100px; margin:0 auto; padding:24px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin-bottom:24px; }}
.card {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:16px; }}
.card .num {{ font-size:26px; font-weight:700; color:var(--accent); }}
.card .lbl {{ font-size:12px; color:var(--text2); margin-top:4px; }}
section {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:20px; margin-bottom:20px; }}
section h2 {{ font-size:15px; margin-bottom:14px; color:var(--accent); }}
form {{ display:flex; flex-wrap:wrap; gap:10px; align-items:end; }}
label {{ font-size:12px; color:var(--text2); display:flex; flex-direction:column; gap:4px; }}
select,input {{ background:var(--surface2); border:1px solid var(--line); color:var(--text); padding:8px 10px; border-radius:6px; font-size:14px; min-width:140px; }}
input:focus,select:focus {{ outline:none; border-color:var(--primary); }}
button {{ background:var(--primary); color:#fff; border:none; padding:9px 18px; border-radius:6px; font-size:14px; cursor:pointer; font-weight:600; }}
button:hover {{ filter:brightness(1.1); }}
button.ghost {{ background:var(--surface2); border:1px solid var(--line); }}
button.danger {{ background:var(--danger); }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ text-align:left; color:var(--text2); font-weight:600; padding:8px 10px; border-bottom:1px solid var(--line); }}
td {{ padding:8px 10px; border-bottom:1px solid var(--line); }}
tr:hover td {{ background:var(--surface2); }}
.k {{ font-family:Consolas,monospace; color:var(--accent); }}
.pill {{ padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }}
.pill.trial {{ background:#3a2f10; color:var(--warn); }}
.pill.halfyear {{ background:#10303a; color:var(--accent); }}
.pill.year {{ background:#1a2a4a; color:#7ba7ff; }}
.pill.lifetime {{ background:#103a24; color:var(--success); }}
.pill.revoked {{ background:#3a1020; color:var(--danger); }}
.newkey {{ background:#103a24; border:1px solid var(--success); border-radius:8px; padding:14px; margin-top:14px; display:none; }}
.newkey.show {{ display:block; }}
.newkey .key {{ font-family:Consolas,monospace; font-size:20px; color:var(--success); letter-spacing:1px; margin:8px 0; }}
.muted {{ color:var(--text2); font-size:12px; }}
.toolbar {{ display:flex; gap:8px; margin-top:14px; }}
</style>
</head>
<body>
<header>
  <h1>💰 Retro+ Satış Paneli</h1>
  <span class="badge">Yerel · {HOST}:{PORT}</span>
</header>
<div class="wrap">
{body}
</div>
</body>
</html>"""
    return html.encode("utf-8")


def _dashboard() -> bytes:
    stats = registry_stats()
    bk = stats.get("by_kind", {})
    body = f"""
<div class="cards">
  <div class="card"><div class="num">{stats['total']}</div><div class="lbl">Toplam anahtar</div></div>
  <div class="card"><div class="num">{stats['issued']}</div><div class="lbl">Aktif (issued)</div></div>
  <div class="card"><div class="num">{stats['revoked']}</div><div class="lbl">İptal edilen</div></div>
  <div class="card"><div class="num">{bk.get('trial', 0)}</div><div class="lbl">Deneme</div></div>
  <div class="card"><div class="num">{bk.get('halfyear', 0)}</div><div class="lbl">6 Aylık</div></div>
  <div class="card"><div class="num">{bk.get('year', 0)}</div><div class="lbl">1 Yıllık</div></div>
  <div class="card"><div class="num">{bk.get('lifetime', 0)}</div><div class="lbl">Ömür Boyu</div></div>
</div>

<section>
  <h2>🔑 Yeni Lisans Anahtarı Üret</h2>
  <form method="post" action="/issue">
    <label>Tür
      <select name="kind">
        <option value="trial">Deneme — {TRIAL_DOWNLOADS} indirme (Ücretsiz)</option>
        <option value="halfyear" selected>6 Aylık — {PRICING['halfyear']}</option>
        <option value="year">1 Yıllık — {PRICING['year']}</option>
        <option value="lifetime">Ömür Boyu — {PRICING['lifetime']}</option>
      </select>
    </label>
    <label>Cihaz
      <select name="seats">
        <option value="1">1</option>
        <option value="2">2</option>
        <option value="3" selected>3</option>
        <option value="5">5</option>
      </select>
    </label>
    <label>Müşteri
      <input type="text" name="customer" placeholder="Ad Soyad / e-posta" style="min-width:200px">
    </label>
    <label>Not
      <input type="text" name="note" placeholder="İsteğe bağlı">
    </label>
    <button type="submit">Üret</button>
  </form>
  <div class="newkey" id="newkey">
    <div class="muted">Üretilen anahtar (müşteriye verin):</div>
    <div class="key" id="newkeyval"></div>
    <div class="muted">Kopyalamak için tıklayın → <code>document.getElementById('newkeyval').textContent</code></div>
  </div>
</section>

<section>
  <h2>📋 Anahtar Listesi</h2>
  <table>
    <tr><th>Anahtar</th><th>Tür</th><th>Cihaz</th><th>Müşteri</th><th>Tarih</th><th>Durum</th><th></th></tr>
"""

    records = list_keys()
    for rec in records:
        kind = rec.get("kind", "?")
        cls = "revoked" if rec.get("status") == "revoked" else kind
        label = KIND_LABELS.get(kind, kind)
        date = rec.get("issued_at", "")[:10]
        customer = rec.get("customer", "") or "—"
        note = rec.get("note", "")
        revoke_btn = ""
        if rec.get("status") != "revoked":
            revoke_btn = (
                f'<form method="post" action="/revoke" style="display:inline">'
                f'<input type="hidden" name="key" value="{rec.get("key", "")}">'
                f'<button class="danger" style="padding:4px 10px;font-size:12px">İptal</button>'
                f'</form>')
        body += (f'<tr><td class="k">{rec.get("key", "")}</td>'
                 f'<td><span class="pill {cls}">{label}</span></td>'
                 f'<td>{rec.get("seats", 1)}</td>'
                 f'<td>{customer}{(" · " + note) if note else ""}</td>'
                 f'<td>{date}</td>'
                 f'<td>{"İptal" if rec.get("status") == "revoked" else "Aktif"}</td>'
                 f'<td>{revoke_btn}</td></tr>\n')

    if not records:
        body += '<tr><td colspan="7" class="muted">Henüz anahtar üretilmedi.</td></tr>'

    body += """
  </table>
  <div class="toolbar">
    <a href="/export.csv"><button class="ghost">⬇ CSV dışa aktar</button></a>
    <a href="/"><button class="ghost">↻ Yenile</button></a>
  </div>
</section>

<section>
  <h2>ℹ️ Fiyatlandırma Özeti</h2>
  <table>
    <tr><th>Tür</th><th>Süre / Hak</th><th>Fiyat</th></tr>
    <tr><td><span class="pill trial">Deneme</span></td><td>{TRIAL_DOWNLOADS} indirme</td><td>Ücretsiz</td></tr>
    <tr><td><span class="pill halfyear">6 Aylık</span></td><td>183 gün, sınırsız indirme</td><td>₺79</td></tr>
    <tr><td><span class="pill year">1 Yıllık</span></td><td>365 gün, sınırsız indirme</td><td>₺119</td></tr>
    <tr><td><span class="pill lifetime">Ömür Boyu</span></td><td>Süresiz, sınırsız indirme</td><td>₺149</td></tr>
  </table>
  <p class="muted" style="margin-top:10px">
    Anahtarlar HMAC-SHA256 ile imzalanır, çevrimdışı doğrulanır.
    Müşteriye anahtarı verin; uygulama içinde <em>Yardım → Lisans</em> menüsünden etkinleştirir.
  </p>
</section>
"""
    return _page("Panel", body)


def _handle_issue(form: dict) -> bytes:
    kind = form.get("kind", ["lifetime"])[0]
    seats_raw = form.get("seats", ["3"])[0]
    customer = (form.get("customer", [""])[0] or "").strip()
    note = (form.get("note", [""])[0] or "").strip()
    if kind not in KIND_CODES:
        return _page("Hata", '<section><h2>Hata</h2><p>Geçersiz tür.</p></section>')
    try:
        seats = max(1, min(9, int(seats_raw)))
    except ValueError:
        seats = 3
    rec = issue_key(kind, seats, customer, note)
    if not rec:
        return _page("Hata", '<section><h2>Hata</h2><p>Üretim başarısız.</p></section>')
    # Dashboard'a dön + yeni anahtar vurgusu
    body = f"""
<section style="border-color:var(--success)">
  <h2>✅ Anahtar Üretildi</h2>
  <div class="key" style="font-family:Consolas,monospace;font-size:22px;color:var(--success);letter-spacing:1px;margin:10px 0">{rec['key']}</div>
  <p class="muted">Tür: {KIND_LABELS.get(kind, kind)} · Cihaz: {seats} ·
     Müşteri: {customer or '—'} · Not: {note or '—'}</p>
  <p class="muted" style="margin-top:8px">Bu anahtarı müşteriye verin (e-posta, mesaj vb.).</p>
  <div class="toolbar">
    <a href="/"><button>← Panele dön</button></a>
    <a href="/export.csv"><button class="ghost">⬇ CSV dışa aktar</button></a>
  </div>
</section>"""
    return _page("Üretildi", body)


def _handle_revoke(form: dict) -> bytes:
    key = (form.get("key", [""])[0] or "").strip()
    if key:
        revoke_key(key)
    # Listeye dön
    return _dashboard()


def _export_csv() -> tuple[str, bytes]:
    records = list_keys()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["key", "kind", "seats", "customer", "note", "issued_at", "status"])
    for rec in reversed(records):
        w.writerow([rec.get("key", ""), rec.get("kind", ""), rec.get("seats", ""),
                    rec.get("customer", ""), rec.get("note", ""),
                    rec.get("issued_at", ""), rec.get("status", "")])
    return "text/csv; charset=utf-8", buf.getvalue().encode("utf-8-sig")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, ctype: str, data: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", _dashboard())
        elif parsed.path == "/export.csv":
            ctype, data = _export_csv()
            self._send(200, ctype, data)
        else:
            self._send(404, "text/plain; charset=utf-8", b"Not Found")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8", "replace")
        form = parse_qs(raw)
        parsed = urlparse(self.path)
        if parsed.path == "/issue":
            self._send(200, "text/html; charset=utf-8", _handle_issue(form))
        elif parsed.path == "/revoke":
            self._send(200, "text/html; charset=utf-8", _handle_revoke(form))
        else:
            self._send(404, "text/plain; charset=utf-8", b"Not Found")

    def log_message(self, fmt, *args):
        pass  # sessiz


def main():
    server = HTTPServer((HOST, PORT), Handler)
    print(f"💰 Retro+ Satış Paneli → http://{HOST}:{PORT}")
    print("   Durdurmak için Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDurduruldu.")


if __name__ == "__main__":
    main()
