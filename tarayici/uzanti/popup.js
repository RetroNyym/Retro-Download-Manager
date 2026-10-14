const $ = (id) => document.getElementById(id);

function kopruYaz(kopruVar, port) {
  const el = $("kopruDurum");
  if (kopruVar) {
    el.textContent = "Retro+ köprüsü bağlı (port " + port + ")";
    el.className = "kontrol";
  } else {
    el.textContent = "Retro+ Download Manager çalışmıyor — programı açın";
    el.className = "kontrol yok";
  }
}

function kuyrukYaz(k) {
  $("kuyruk").textContent =
    "Kuyruk: " +
    (k.queued || 0) +
    "  |  İnen: " +
    (k.active || 0) +
    "  |  Tamam: " +
    (k.completed || 0) +
    "  |  Toplam: " +
    (k.total || 0);
}

function listeCiz(sonuclar) {
  const kutu = $("liste");
  kutu.innerHTML = "";
  if (!sonuclar || !sonuclar.length) {
    kutu.innerHTML =
      '<div class="bos">Henüz aktarım yok.<br>Tarayıcıda bir dosya indirin — Retro+ yakalar.</div>';
    return;
  }
  sonuclar.slice(0, 50).forEach((k) => {
    const d = document.createElement("div");
    d.className = "kayit";
    const et = k.ok ? "tamam" : "hata";
    const etTxt = k.ok ? "Retro+\'a aktarıldı" : "Hata";
    d.innerHTML =
      '<div class="ad" title="' +
      k.dosya.replace(/"/g, "&quot;") +
      '">' +
      k.dosya +
      "</div>" +
      '<div class="alt"><span class="etiket ' +
      et +
      '">' +
      etTxt +
      "</span><span>" +
      k.zaman +
      "</span></div>" +
      (k.hata
        ? '<div class="alt" style="color:#c5221f">' + k.hata + "</div>"
        : "");
    kutu.appendChild(d);
  });
}

chrome.runtime.sendMessage({ cmd: "get" }, (yanit) => {
  if (chrome.runtime.lastError || !yanit) {
    kopruYaz(false);
    return;
  }
  $("yakala").checked = !!yanit.yakala;
  kopruYaz(yanit.kopruVar, yanit.port);
  kuyrukYaz(yanit.kuyruk || {});
  listeCiz(yanit.sonuclar);
});

$("yakala").addEventListener("change", (e) => {
  chrome.runtime.sendMessage({ cmd: "yakala", deger: e.target.checked });
});

$("yenile").addEventListener("click", () => {
  chrome.runtime.sendMessage({ cmd: "yenile" }, (yanit) => {
    if (yanit && yanit.ok) {
      kopruYaz(yanit.kopruVar, yanit.port);
      kuyrukYaz(yanit.kuyruk || {});
    }
  });
});
