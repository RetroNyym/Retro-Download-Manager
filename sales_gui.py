"""Retro+ Satış Paneli — Masaüstü GUI (Tkinter).

Çoklu ürün: Retro+ Download Manager, Video Editor, Music Audio, File Converter.
Her ürünün kendi ön eki, fiyatları ve anahtarları vardır.

Çalıştırma:
    python sales_gui.py

İşlevler:
  • Ürün seçimi (dropdown)
  • Yeni anahtar üretme (tür, cihaz, müşteri, not)
  • Panoya kopyalama
  • Anahtar listesi (ürüne göre filtre)
  • İptal etme
  • CSV dışa aktarma
  • İstatistikler
"""

from __future__ import annotations

import csv
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from download_manager.license import (  # noqa: E402
    issue_key, list_keys, revoke_key, registry_stats,
    load_products, KIND_LABELS_TR,
)

# ─── Renk paleti (koyu tema) ────────────────────────────────────────────────
C = {
    "bg": "#0f1115",
    "surface": "#161920",
    "surface2": "#1c2028",
    "surface3": "#232833",
    "line": "#2b3140",
    "text": "#e8ebf0",
    "text2": "#9aa3b2",
    "text3": "#5c6470",
    "primary": "#6c7bff",
    "accent": "#3ec6e0",
    "success": "#3ddc84",
    "danger": "#ff5c72",
    "warn": "#ffb020",
}

KIND_COLORS = {
    "trial": C["warn"],
    "halfyear": C["accent"],
    "year": "#7ba7ff",
    "lifetime": C["success"],
}

PRODUCT_COLORS = {
    "Retro+ Download Manager": "#6c7bff",
    "Retro+ Video Editor": "#ff6c9f",
    "Retro+ Music Audio": "#3ddc84",
    "Retro+ File Converter": "#ffb020",
}


class SalesGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔑 Retro+ Satış Paneli")
        self.root.configure(bg=C["bg"])
        self.root.geometry("1050x720")
        self.root.minsize(900, 600)

        self.products = load_products()
        self._photos = []

        self._build_ui()
        self._refresh_list()
        self._refresh_stats()

    # ─── UI kurulumu ────────────────────────────────────────────────────────

    def _build_ui(self):
        # Başlık çubuğu
        header = tk.Frame(self.root, bg=C["surface"], height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🔑 Retro+ Satış Paneli",
                 bg=C["surface"], fg=C["text"],
                 font=("Segoe UI Semibold", 15)).pack(side="left", padx=16)
        tk.Label(header, text=f"{len(self.products)} ürün yüklü",
                 bg=C["surface"], fg=C["text3"],
                 font=("Segoe UI", 9)).pack(side="right", padx=16)

        # Gövde
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=10)

        # Sol panel: üretim formu
        left = tk.Frame(body, bg=C["bg"], width=320)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        # Sağ panel: liste + istatistik
        right = tk.Frame(body, bg=C["bg"])
        right.pack(side="right", fill="both", expand=True)

        self._build_issue_panel(left)
        self._build_stats_panel(left)
        self._build_contact_panel(left)
        self._build_list_panel(right)

    def _build_issue_panel(self, parent):
        card = tk.Frame(parent, bg=C["surface"], padx=16, pady=14)
        card.pack(fill="x", pady=(0, 10))
        tk.Label(card, text="Yeni Anahtar Üret", bg=C["surface"],
                 fg=C["accent"], font=("Segoe UI Semibold", 12)).pack(anchor="w")

        # Ürün
        tk.Label(card, text="Ürün", bg=C["surface"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 2))
        self.var_product = tk.StringVar()
        product_names = [info["name"] for info in self.products.values()]
        self.cmb_product = ttk.Combobox(card, textvariable=self.var_product,
                                        values=product_names, state="readonly")
        self.cmb_product.pack(fill="x", ipady=4)
        self.cmb_product.set(product_names[0])
        self.cmb_product.bind("<<ComboboxSelected>>", self._on_product)

        # Tür
        tk.Label(card, text="Lisans Türü", bg=C["surface"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 2))
        self.var_kind = tk.StringVar()
        kind_labels = []
        self._kind_map = {}
        for kind_code, label in KIND_LABELS_TR.items():
            display = f"{label} — {self._price_for(kind_code)}"
            kind_labels.append(display)
            self._kind_map[display] = kind_code
        self.cmb_kind = ttk.Combobox(card, textvariable=self.var_kind,
                                     values=kind_labels, state="readonly")
        self.cmb_kind.pack(fill="x", ipady=4)
        self.cmb_kind.set(kind_labels[2] if len(kind_labels) > 2 else kind_labels[0])

        # Cihaz
        tk.Label(card, text="Cihaz Sayısı", bg=C["surface"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 2))
        self.var_seats = tk.StringVar(value="3")
        cmb_seats = ttk.Combobox(card, textvariable=self.var_seats,
                                 values=["1", "2", "3", "4", "5", "6", "7", "8", "9"],
                                 state="readonly", width=8)
        cmb_seats.pack(anchor="w", ipady=4)

        # Müşteri
        tk.Label(card, text="Müşteri", bg=C["surface"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 2))
        self.var_customer = tk.StringVar()
        tk.Entry(card, textvariable=self.var_customer, bg=C["surface2"],
                 fg=C["text"], insertbackground=C["text"], relief="flat",
                 font=("Segoe UI", 10)).pack(fill="x", ipady=5)

        # Not
        tk.Label(card, text="Not (isteğe bağlı)", bg=C["surface"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 2))
        self.var_note = tk.StringVar()
        tk.Entry(card, textvariable=self.var_note, bg=C["surface2"],
                 fg=C["text"], insertbackground=C["text"], relief="flat",
                 font=("Segoe UI", 10)).pack(fill="x", ipady=5)

        # Üret butonu
        tk.Button(card, text="🔑  Üret", command=self._issue,
                  bg=C["primary"], fg="#fff", activebackground="#5a68e0",
                  activeforeground="#fff", relief="flat", font=("Segoe UI", 10, "bold"),
                  padx=20, pady=6, cursor="hand2").pack(fill="x", pady=(14, 0))

        # Üretilen anahtar kutusu
        self.frame_result = tk.Frame(parent, bg=C["surface"], padx=16, pady=12)
        self.frame_result.pack(fill="x", pady=(0, 10))
        self.frame_result.pack_forget()
        tk.Label(self.frame_result, text="Üretilen anahtar:",
                 bg=C["surface"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(anchor="w")
        self.lbl_newkey = tk.Label(self.frame_result, text="",
                                   bg=C["surface"], fg=C["success"],
                                   font=("Consolas", 14, "bold"), wraplength=280)
        self.lbl_newkey.pack(anchor="w", pady=4)
        tk.Button(self.frame_result, text="📋 Panoya Kopyala",
                  command=self._copy_newkey, bg=C["surface3"], fg=C["text"],
                  activebackground=C["line"], relief="flat",
                  font=("Segoe UI", 9), padx=10, pady=3, cursor="hand2").pack(anchor="w")

    def _build_stats_panel(self, parent):
        card = tk.Frame(parent, bg=C["surface"], padx=16, pady=14)
        card.pack(fill="x")
        tk.Label(card, text="İstatistik", bg=C["surface"],
                 fg=C["accent"], font=("Segoe UI Semibold", 12)).pack(anchor="w")
        self.lbl_stats = tk.Label(card, text="Yükleniyor...",
                                  bg=C["surface"], fg=C["text2"],
                                  font=("Segoe UI", 9), justify="left")
        self.lbl_stats.pack(anchor="w", pady=(8, 0))

    def _build_contact_panel(self, parent):
        """Satış iletişim bilgileri (contact.json'dan okunur)."""
        card = tk.Frame(parent, bg=C["surface"], padx=16, pady=14)
        card.pack(fill="x", pady=(10, 0))
        tk.Label(card, text="📨 Satış İletişimi", bg=C["surface"],
                 fg=C["accent"], font=("Segoe UI Semibold", 12)).pack(anchor="w")

        contact = self._load_contact()
        rows = [
            ("E-posta", contact.get("email", "")),
            ("WhatsApp", contact.get("whatsapp", "")),
            ("Alıcı", contact.get("holder", "")),
            ("IBAN", contact.get("iban", "")),
            ("Banka", contact.get("bank", "")),
            ("Papara", contact.get("papara", "")),
        ]
        for label, value in rows:
            if not value:
                continue
            row = tk.Frame(card, bg=C["surface"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"{label}:", bg=C["surface"], fg=C["text3"],
                     font=("Segoe UI", 9), width=10, anchor="w").pack(side="left")
            lbl = tk.Label(row, text=value, bg=C["surface"], fg=C["text"],
                           font=("Consolas", 9), anchor="w")
            lbl.pack(side="left", fill="x")
            # Kopyala butonu
            tk.Button(row, text="📋", command=lambda v=value: self._copy_text(v),
                      bg=C["surface3"], fg=C["text2"], relief="flat",
                      font=("Segoe UI", 8), padx=4, pady=0, cursor="hand2").pack(side="right")

        tk.Button(card, text="📧 Sipariş E-postası Gönder",
                  command=lambda: self._open_email_composer(contact),
                  bg=C["success"], fg="#fff", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=5,
                  cursor="hand2").pack(fill="x", pady=(10, 0))

        if not any(contact.values()):
            tk.Label(card, text="İletişim bilgileri için sales/contact.json dosyasını düzenleyin.",
                     bg=C["surface"], fg=C["text3"], font=("Segoe UI", 8),
                     wraplength=260).pack(anchor="w", pady=(6, 0))

    def _load_contact(self) -> dict:
        path = Path(__file__).resolve().parent / "sales" / "contact.json"
        try:
            import json
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _copy_text(self, text: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Kopyalandı", f"{text} panoya kopyalandı.")

    def _open_email_composer(self, contact: dict):
        """Varsayılan e-posta istemcisinde sipariş taslağı açar."""
        email = contact.get("email", "")
        subject = "Retro+ Lisans Siparişi"
        body = ("Merhaba,\n\n"
                "Retro+ lisans satın almak istiyorum.\n\n"
                "Ad Soyad: \n"
                "Ürün: \n"
                "Tür (6 Aylık / Yıllık / Ömür Boyu): \n"
                "Ödeme yöntemi: \n"
                "Dekont: eklendi\n")
        import urllib.parse
        mailto = f"mailto:{email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        import webbrowser
        webbrowser.open(mailto)

    def _build_list_panel(self, parent):
        card = tk.Frame(parent, bg=C["surface"], padx=12, pady=12)
        card.pack(fill="both", expand=True)

        # Üst bar: filtre + butonlar
        bar = tk.Frame(card, bg=C["surface"])
        bar.pack(fill="x", pady=(0, 8))
        tk.Label(bar, text="Ürün filtresi:", bg=C["surface"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(side="left")
        self.var_filter = tk.StringVar(value="Tümü")
        products = ["Tümü"] + [p["name"] for p in self.products.values()]
        cmb = ttk.Combobox(bar, textvariable=self.var_filter, values=products,
                           state="readonly", width=28)
        cmb.pack(side="left", padx=(6, 12))
        cmb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_list())

        tk.Button(bar, text="⬇ CSV", command=self._export_csv,
                  bg=C["surface3"], fg=C["text"], relief="flat",
                  font=("Segoe UI", 9), padx=10, pady=3, cursor="hand2").pack(side="right", padx=4)
        tk.Button(bar, text="🔄 Yenile", command=self._refresh_list,
                  bg=C["surface3"], fg=C["text"], relief="flat",
                  font=("Segoe UI", 9), padx=10, pady=3, cursor="hand2").pack(side="right", padx=4)

        # Tablo
        cols = ("key", "product", "kind", "seats", "customer", "date", "status")
        heads = ("Anahtar", "Ürün", "Tür", "Cihaz", "Müşteri", "Tarih", "Durum")
        widths = (240, 170, 90, 50, 130, 90, 70)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview", background=C["surface2"],
                        fieldbackground=C["surface2"], foreground=C["text"],
                        rowheight=28, font=("Consolas", 9))
        style.configure("Dark.Treeview.Heading", background=C["surface3"],
                        foreground=C["text2"], font=("Segoe UI", 9, "bold"))
        style.map("Dark.Treeview", background=[("selected", C["primary"])],
                  foreground=[("selected", "#fff")])

        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                 style="Dark.Treeview", selectmode="browse")
        for col, head, w in zip(cols, heads, widths):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, minwidth=50)
        self.tree.tag_configure("revoked", foreground=C["danger"])
        self.tree.tag_configure("trial", foreground=C["warn"])
        self.tree.tag_configure("lifetime", foreground=C["success"])

        scrollbar = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sağ tık menüsü
        self.menu = tk.Menu(self.root, tearoff=0, bg=C["surface2"],
                            fg=C["text"], activebackground=C["primary"],
                            font=("Segoe UI", 9))
        self.menu.add_command(label="📋 Panoya Kopyala", command=self._copy_selected)
        self.menu.add_command(label="❌ İptal Et", command=self._revoke_selected)
        self.tree.bind("<Button-3>", self._on_right_click)

        # Alt butonlar
        bottom = tk.Frame(card, bg=C["surface"])
        bottom.pack(fill="x", pady=(8, 0))
        tk.Button(bottom, text="📋 Seçileni Kopyala", command=self._copy_selected,
                  bg=C["surface3"], fg=C["text"], relief="flat",
                  font=("Segoe UI", 9), padx=10, pady=4, cursor="hand2").pack(side="left", padx=4)
        tk.Button(bottom, text="❌ Seçileni İptal Et", command=self._revoke_selected,
                  bg=C["danger"], fg="#fff", relief="flat",
                  font=("Segoe UI", 9), padx=10, pady=4, cursor="hand2").pack(side="left", padx=4)

    # ─── Mantık ─────────────────────────────────────────────────────────────

    def _current_product_code(self) -> int:
        name = self.var_product.get()
        for code, info in self.products.items():
            if info["name"] == name:
                return code
        return 1

    def _price_for(self, kind: str) -> str:
        code = self._current_product_code()
        info = self.products.get(code, {})
        return info.get("prices", {}).get(kind, "")

    def _on_product(self, _event=None):
        # Tür fiyatlarını güncelle
        kind_labels = []
        for kind_code, label in KIND_LABELS_TR.items():
            display = f"{label} — {self._price_for(kind_code)}"
            kind_labels.append(display)
            self._kind_map[display] = kind_code
        self.cmb_kind.configure(values=kind_labels)
        current = self.var_kind.get()
        if current not in kind_labels:
            self.cmb_kind.set(kind_labels[2] if len(kind_labels) > 2 else kind_labels[0])

    def _issue(self):
        product_code = self._current_product_code()
        kind_display = self.var_kind.get()
        kind = self._kind_map.get(kind_display, "lifetime")
        try:
            seats = max(1, min(9, int(self.var_seats.get())))
        except ValueError:
            seats = 3
        customer = self.var_customer.get().strip()
        note = self.var_note.get().strip()

        rec = issue_key(kind, seats, customer, note, product_code)
        if not rec:
            messagebox.showerror("Hata", "Anahtar üretilemedi.")
            return

        self._newkey = rec["key"]
        self.lbl_newkey.configure(text=rec["key"])
        self.frame_result.pack(fill="x", pady=(0, 10))

        self.var_customer.set("")
        self.var_note.set("")
        self._refresh_list()
        self._refresh_stats()

    def _copy_newkey(self):
        key = getattr(self, "_newkey", "")
        if key:
            self.root.clipboard_clear()
            self.root.clipboard_append(key)
            messagebox.showinfo("Kopyalandı", f"{key} panoya kopyalandı.")

    def _copy_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        key = self.tree.item(sel[0], "values")[0]
        self.root.clipboard_clear()
        self.root.clipboard_append(key)
        messagebox.showinfo("Kopyalandı", f"{key} panoya kopyalandı.")

    def _revoke_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        key = self.tree.item(sel[0], "values")[0]
        if messagebox.askyesno("İptal", f"{key} iptal edilsin mi?"):
            revoke_key(key)
            self._refresh_list()
            self._refresh_stats()

    def _on_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.menu.tk_popup(event.x_root, event.y_root)

    def _refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        filter_product = self.var_filter.get()
        for rec in list_keys():
            product = rec.get("product", "?")
            if filter_product != "Tümü" and product != filter_product:
                continue
            kind = rec.get("kind", "?")
            status = rec.get("status", "issued")
            date = rec.get("issued_at", "")[:10]
            tags = []
            if status == "revoked":
                tags.append("revoked")
            else:
                tags.append(kind)
            self.tree.insert("", "end", tags=tags, values=(
                rec.get("key", ""),
                product,
                KIND_LABELS_TR.get(kind, kind),
                rec.get("seats", 1),
                rec.get("customer", "") or "—",
                date,
                "İptal" if status == "revoked" else "Aktif",
            ))

    def _refresh_stats(self):
        stats = registry_stats()
        lines = [
            f"Toplam: {stats['total']}  ·  Aktif: {stats['issued']}  ·  İptal: {stats['revoked']}",
            "",
        ]
        for product, count in stats.get("by_product", {}).items():
            lines.append(f"  • {product}: {count}")
        lines.append("")
        for kind, count in stats.get("by_kind", {}).items():
            label = KIND_LABELS_TR.get(kind, kind)
            lines.append(f"  • {label}: {count}")
        self.lbl_stats.configure(text="\n".join(lines) if lines else "Kayıt yok")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Tümü", "*.*")],
            initialfile=f"retro-sales-{datetime.now():%Y%m%d}.csv")
        if not path:
            return
        records = list_keys()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["key", "product", "kind", "seats", "customer",
                        "note", "issued_at", "status"])
            for rec in reversed(records):
                w.writerow([rec.get("key", ""), rec.get("product", ""),
                            rec.get("kind", ""), rec.get("seats", ""),
                            rec.get("customer", ""), rec.get("note", ""),
                            rec.get("issued_at", ""), rec.get("status", "")])
        messagebox.showinfo("Dışa Aktarıldı", f"{len(records)} kayıt → {path}")

    def run(self):
        self.root.mainloop()


def main():
    app = SalesGUI()
    app.run()


if __name__ == "__main__":
    main()
