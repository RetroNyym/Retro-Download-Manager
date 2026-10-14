// Retro+ Tarayıcı Modülü — indirme yakalama (service worker).
// Chrome/Edge bir indirme başlatınca iptal eder ve URL'i yerel
// Retro+ Download Manager köprüsüne (127.0.0.1:8877/add) gönderir;
// dosyayı Retro+ motoru indirir, arayüzde görünür.

const PORT_BAS = 8877;
const PORT_SON = 8899;
const SON_LIMITE = 50;

let yakala = true;
let kopruVar = false;
let bulunanPort = null;
let sonucListesi = [];
let kuyruk = { active: 0, queued: 0, completed: 0, total: 0 };

chrome.storage.local.get(["yakala", "sonuclar"], (v) => {
  if (typeof v.yakala === "boolean") yakala = v.yakala;
  if (Array.isArray(v.sonuclar)) sonucListesi = v.sonuclar;
  rozetGuncelle();
});

function kaydet() {
  chrome.storage.local.set({ sonuclar: sonucListesi.slice(0, SON_LIMITE) });
}

function portBul(geri) {
  if (bulunanPort && !geri) return Promise.resolve(bulunanPort);
  return new Promise((resolve) => {
    chrome.storage.local.get(["kopruPort"], (v) => {
      const sira = [];
      const kayitli = Number(v.kopruPort);
      if (kayitli >= PORT_BAS && kayitli <= PORT_SON) sira.push(kayitli);
      for (let p = PORT_BAS; p <= PORT_SON; p++) {
        if (!sira.includes(p)) sira.push(p);
      }
      const dene = (i) => {
        if (i >= sira.length) {
          kopruVar = false;
          resolve(null);
          return;
        }
        const p = sira[i];
        fetch("http://127.0.0.1:" + p + "/status", { cache: "no-store" })
          .then((r) => r.json())
          .then((j) => {
            if (j && j.ok) {
              bulunanPort = p;
              kopruVar = true;
              chrome.storage.local.set({ kopruPort: p });
              resolve(p);
            } else {
              dene(i + 1);
            }
          })
          .catch(() => dene(i + 1));
      };
      dene(0);
    });
  });
}

function istek(yol) {
  return portBul().then((port) => {
    if (!port) return { ok: false, error: "Retro+ köprüsü bulunamadı" };
    return fetch("http://127.0.0.1:" + port + yol, { cache: "no-store" })
      .then((r) => r.json())
      .catch((e) => {
        bulunanPort = null;
        kopruVar = false;
        rozetGuncelle();
        return { ok: false, error: String(e) };
      });
  });
}

function rozetGuncelle() {
  if (!kopruVar) {
    chrome.action.setBadgeText({ text: "!" });
    chrome.action.setBadgeBackgroundColor({ color: "#c5221f" });
    return;
  }
  if (!yakala) {
    chrome.action.setBadgeText({ text: "" });
    return;
  }
  if (kuyruk.active > 0) {
    chrome.action.setBadgeText({ text: String(kuyruk.active) });
    chrome.action.setBadgeBackgroundColor({ color: "#0b57d0" });
  } else {
    chrome.action.setBadgeText({ text: "+" });
    chrome.action.setBadgeBackgroundColor({ color: "#0e2a3f" });
  }
}

function adSade(url, istenen) {
  if (istenen) {
    const p = istenen.split(/[\\/]/).filter(Boolean);
    if (p.length) return p[p.length - 1];
  }
  try {
    const u = new URL(url);
    const p = u.pathname.split("/").filter(Boolean);
    return p.length ? p[p.length - 1] : "indirilen";
  } catch (e) {
    return "indirilen";
  }
}

// ---- indirme yakalama ------------------------------------------------------
chrome.downloads.onCreated.addListener((item) => {
  if (!yakala) return;
  if (!item || !item.url) return;
  if (item.url.startsWith("chrome-extension://")) return;
  if (item.byExtensionId === chrome.runtime.id) return;
  if (!/^https?:/i.test(item.url)) return;

  chrome.downloads.cancel(item.id).catch(() => {});

  const dosya = adSade(item.url, item.filename);
  istek("/add?url=" + encodeURIComponent(item.url)).then((yanit) => {
    sonucListesi.unshift({
      zaman: new Date().toLocaleString("tr-TR"),
      url: item.url,
      dosya: (yanit && yanit.filename) || dosya,
      id: (yanit && yanit.id) || "",
      ok: !!(yanit && yanit.ok),
      hata: (yanit && yanit.error) || ""
    });
    sonucListesi = sonucListesi.slice(0, SON_LIMITE);
    kaydet();
    durumTazele();
  });
});

// ---- periyodik durum (rozet) ----------------------------------------------
function durumTazele() {
  return istek("/status").then((yanit) => {
    if (yanit && yanit.ok) {
      kopruVar = true;
      kuyruk = {
        active: yanit.active || 0,
        queued: yanit.queued || 0,
        completed: yanit.completed || 0,
        total: yanit.total || 0
      };
    } else {
      kopruVar = false;
    }
    rozetGuncelle();
  });
}

chrome.alarms.create("durum", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((a) => {
  if (a.name === "durum") durumTazele();
});
chrome.runtime.onStartup.addListener(() => durumTazele());
chrome.runtime.onInstalled.addListener(() => durumTazele());

// ---- popup mesajlari -------------------------------------------------------
chrome.runtime.onMessage.addListener((mesaj, gonderen, cevap) => {
  if (!mesaj || !mesaj.cmd) return;
  if (mesaj.cmd === "get") {
    durumTazele().then(() =>
      cevap({
        yakala,
        kopruVar,
        port: bulunanPort,
        kuyruk,
        sonuclar: sonucListesi
      })
    );
    return true;
  }
  if (mesaj.cmd === "yakala") {
    yakala = !!mesaj.deger;
    chrome.storage.local.set({ yakala });
    rozetGuncelle();
    cevap({ ok: true, yakala });
    return true;
  }
  if (mesaj.cmd === "yenile") {
    bulunanPort = null;
    durumTazele().then(() =>
      cevap({ ok: true, kopruVar, port: bulunanPort, kuyruk })
    );
    return true;
  }
});
