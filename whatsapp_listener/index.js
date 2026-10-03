/* Retro+ WhatsApp PDF dinleyici
 * Telefonu "bagli cihaz" olarak QR ile esler; yalnizca config.json'daki
 * beyaz listedeki grup/kişilerden gelen PDF'leri indirip
 * watchFolder icine koyar (yanina <dosya>.pdf.json ustu veri yazar).
 * Python tarafindaki download_manager.whatsapp modulu oradan alir.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const makeWASocket = require("@whiskeysockets/baileys").default;
const {
  useMultiFileAuthState,
  DisconnectReason,
  downloadMediaMessage,
} = require("@whiskeysockets/baileys");
const qrcode = require("qrcode");
const pino = require("pino");

const ROOT = __dirname;
const CFG = path.join(ROOT, "config.json");
const STATUS = path.join(ROOT, "status.json");
const CHATS = path.join(ROOT, "chats.json");
const QR_PNG = path.join(ROOT, "qr.png");
const SESSION = path.join(ROOT, "session");
const logger = pino({ level: "silent" });

const seenChats = new Map();

function readConfig() {
  try {
    const data = JSON.parse(fs.readFileSync(CFG, "utf8"));
    return {
      watchFolder: String(data.watchFolder || ""),
      whitelist: Array.isArray(data.whitelist) ? data.whitelist : [],
    };
  } catch (_e) {
    return { watchFolder: "", whitelist: [] };
  }
}

function writeStatus(state, extra) {
  const payload = Object.assign({ state: state, time: Date.now() }, extra || {});
  try {
    fs.writeFileSync(STATUS, JSON.stringify(payload, null, 2));
  } catch (_e) { /* yoksay */ }
}

function safeName(name) {
  const base = path.basename(String(name || "dosya.pdf"));
  const cleaned = base.replace(/[<>:"/\\|?*\x00-\x1f]+/g, "_").trim();
  return cleaned || "dosya.pdf";
}

function jidBody(jid) {
  return String(jid || "").split("@", 1)[0];
}

function allowed(chat, sender, whitelist) {
  if (!whitelist.length) return false;
  const values = [chat, sender].filter(Boolean);
  for (const entry of whitelist) {
    const needle = String(entry || "").trim();
    if (!needle) continue;
    const body = jidBody(needle);
    for (const value of values) {
      if (value === needle || jidBody(value) === body) return true;
    }
  }
  return false;
}

async function writeChats(sock) {
  const chats = [];
  try {
    const groups = await sock.groupFetchAllParticipating();
    for (const g of Object.values(groups || {})) {
      if (g && g.id) chats.push({ jid: g.id, label: g.subject || g.id, isGroup: true });
    }
  } catch (_e) { /* grup listesi alinamadi */ }
  for (const [jid, info] of seenChats.entries()) {
    chats.push({ jid: jid, label: info.name || jid, isGroup: false });
  }
  try {
    fs.writeFileSync(CHATS, JSON.stringify(chats, null, 2));
  } catch (_e) { /* yoksay */ }
  writeStatus("connected", { chats: chats.length });
  return chats;
}

async function handleDocument(sock, msg) {
  const cfg = readConfig();
  if (!cfg.watchFolder) {
    writeStatus("error", { error: "watchFolder config'de bos" });
    return;
  }
  const chat = msg.key.remoteJid;
  const sender = msg.key.participant || msg.key.remoteJid;
  const content =
    msg.message && (msg.message.documentMessage ||
      (msg.message.documentWithCaptionMessage &&
        msg.message.documentWithCaptionMessage.message &&
        msg.message.documentWithCaptionMessage.message.documentMessage));
  if (!content) return;
  const mime = String(content.mimetype || "").toLowerCase();
  const fileName = String(content.fileName || "dosya.pdf");
  const isPdf = mime === "application/pdf" || /\.pdf$/i.test(fileName);
  if (!isPdf) return; // yalnizca PDF'ler
  if (!allowed(chat, sender, cfg.whitelist)) return; // beyaz liste disi

  try {
    const buffer = await downloadMediaMessage(msg, "buffer", {}, {
      logger: logger,
      reuploadRequest: sock.updateMediaMessage,
    });
    if (!buffer || !buffer.length) return;
    fs.mkdirSync(cfg.watchFolder, { recursive: true });
    const stamp = Date.now();
    const finalName = `${stamp}_${safeName(fileName)}`;
    const finalPath = path.join(cfg.watchFolder, finalName);
    const partPath = finalPath + ".part";
    const label = (seenChats.get(chat) || {}).name || chat;
    const meta = {
      chat: chat,
      sender: sender,
      label: label,
      name: safeName(fileName),
      timestamp: Math.floor(stamp / 1000),
    };
    fs.writeFileSync(partPath, buffer);
    fs.writeFileSync(finalPath + ".json", JSON.stringify(meta, null, 2));
    fs.renameSync(partPath, finalPath); // once ust veri, sonra pdf gorunur
    writeStatus("connected", { lastPdf: finalName });
    console.log("PDF alindi:", finalName, "<-", label);
  } catch (err) {
    console.error("PDF indirme hatasi:", err && err.message ? err.message : err);
    writeStatus("connected", { lastError: String(err && err.message || err) });
  }
}

async function main() {
  if (!fs.existsSync(SESSION)) fs.mkdirSync(SESSION, { recursive: true });
  const { state, saveCreds } = await useMultiFileAuthState(SESSION);
  const sock = makeWASocket({
    auth: state,
    logger: logger,
    printQRInTerminal: false,
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;
    if (qr) {
      try {
        await qrcode.toFile(QR_PNG, qr, { width: 420, margin: 1 });
        writeStatus("waiting_qr", { hint: "Telefonla qr.png karekodunu okutun" });
      } catch (err) {
        writeStatus("waiting_qr", { error: String(err) });
      }
    }
    if (connection === "open") {
      try { fs.unlinkSync(QR_PNG); } catch (_e) { /* zaten yok */ }
      writeStatus("connected");
      await writeChats(sock);
      setInterval(() => { writeChats(sock).catch(() => {}); }, 10 * 60 * 1000);
    }
    if (connection === "close") {
      const code = lastDisconnect &&
        lastDisconnect.error && lastDisconnect.error.output &&
        lastDisconnect.error.output.statusCode;
      if (code === DisconnectReason.loggedOut) {
        writeStatus("logged_out", { error: "Oturum kapandi — QR ile yeniden esleyin" });
        console.log("Cikis yapildi; session klasorunu silip yeniden baslatin.");
        process.exit(0);
      }
      writeStatus("reconnecting");
      setTimeout(() => { main().catch((err) => {
        writeStatus("error", { error: String(err) });
        process.exit(1);
      }); }, 1500);
    }
  });

  sock.ev.on("messages.upsert", async (upsert) => {
    try {
      if (!upsert || upsert.type !== "notify") return;
      for (const msg of upsert.messages || []) {
        if (!msg || !msg.message) continue;
        const chat = msg.key.remoteJid;
        if (chat && chat !== "status@broadcast" && !seenChats.has(chat)) {
          seenChats.set(chat, {
            name: msg.pushName || jidBody(msg.key.participant || chat),
          });
        }
        await handleDocument(sock, msg);
      }
    } catch (err) {
      console.error("mesaj hatasi:", err && err.message ? err.message : err);
    }
  });
}

writeStatus("starting");
main().catch((err) => {
  writeStatus("error", { error: String(err && err.message || err) });
  console.error(err);
  process.exit(1);
});
