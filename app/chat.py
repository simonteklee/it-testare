"""Klasschatt (24 h): enkel delad live-chatt för klassen.

Ingen inloggning behövs:
- **Text** delas via ntfy.sh (gratis, inget konto). Varje meddelande skickas som
  JSON-sträng så att även avsändarnamn och ev. fil-länk följer med.
- **Bilder/filer** laddas upp till litterbox.catbox.moe (anonymt, länken lever 24 h)
  och skickas som en URL i meddelandet.

Meddelanden äldre än 24 timmar filtreras bort (serverns cache rensar dem också).
Allt ligger kvar lokalt i data/chat.jsonl så att man ser hela dygnet även om
serverns cache är kortare.
"""
from __future__ import annotations

import json
import socket
import time
from pathlib import Path

import httpx

from . import feedback

DATA = Path(__file__).resolve().parent.parent / "data"
CHAT_FILE = DATA / "chat.jsonl"

NTFY = "https://ntfy.sh"
LITTERBOX = "https://litterbox.catbox.moe/resources/internals/api.php"
# Gemensamt klassrum (byt vid behov i inställningarna). Ingen hemlighet – men
# ett svårgissat namn så att inte vem som helst råkar hitta in.
DEFAULT_TOPIC = "testarn-klass-8f42c1d9"

TTL = 24 * 3600
MAX_TEXT = 3000


def _cfg() -> dict:
    return feedback.load_config()


def topic() -> str:
    return (_cfg().get("chat_topic") or DEFAULT_TOPIC).strip() or DEFAULT_TOPIC


def my_name() -> str:
    n = (_cfg().get("chat_name") or "").strip()
    if n:
        return n
    try:
        return socket.gethostname().split(".")[0] or "Anonym"
    except Exception:
        return "Anonym"


def enabled() -> bool:
    return bool(_cfg().get("chat_on", True))


# ---- lokal cache ----

def _read_local() -> list[dict]:
    if not CHAT_FILE.exists():
        return []
    out = []
    for line in CHAT_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def _write_local(msgs: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    CHAT_FILE.write_text("".join(json.dumps(m, ensure_ascii=False) + "\n" for m in msgs),
                         encoding="utf-8")


def _parse_message(body: str) -> dict:
    """Meddelandetexten är en JSON-sträng {n,t,u,k}; faller tillbaka på råtext."""
    try:
        d = json.loads(body)
        if isinstance(d, dict) and ("t" in d or "n" in d or "u" in d):
            return {"from": str(d.get("n", "?"))[:40], "text": str(d.get("t", "")),
                    "url": str(d.get("u", "")), "kind": str(d.get("k", ""))}
    except Exception:
        pass
    return {"from": "?", "text": body, "url": "", "kind": ""}


def fetch() -> list[dict]:
    """Hämta klassens meddelanden (ntfy + lokal cache), filtrerat till 24 h."""
    by_id: dict[str, dict] = {}
    for m in _read_local():
        if m.get("id"):
            by_id[m["id"]] = m
    try:
        r = httpx.get(f"{NTFY}/{topic()}/json",
                      params={"poll": "1", "since": "24h"},
                      timeout=12.0, follow_redirects=True)
        if r.status_code == 200:
            for line in r.text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("event") != "message":
                    continue
                mid = obj.get("id")
                if not mid:
                    continue
                p = _parse_message(obj.get("message", ""))
                by_id[mid] = {"id": mid, "ts": obj.get("time", 0), "from": p["from"],
                              "text": p["text"], "url": p["url"], "kind": p["kind"]}
    except Exception:
        pass

    now = time.time()
    msgs = [m for m in by_id.values() if (now - (m.get("ts") or 0)) <= TTL]
    msgs.sort(key=lambda m: m.get("ts", 0))
    try:
        _write_local(msgs)
    except Exception:
        pass
    return msgs


def send(text: str, name: str = "", url: str = "", kind: str = "") -> dict:
    text = (text or "").strip()[:MAX_TEXT]
    if not text and not url:
        raise ValueError("tomt meddelande")
    body = json.dumps({"n": (name or my_name())[:40], "t": text, "u": url, "k": kind},
                      ensure_ascii=False)
    r = httpx.post(f"{NTFY}/{topic()}", content=body.encode("utf-8"),
                   headers={"Content-Type": "text/plain; charset=utf-8"},
                   timeout=15.0, follow_redirects=True)
    if r.status_code != 200:
        raise RuntimeError(f"ntfy {r.status_code}: {r.text[:160]}")
    try:
        d = r.json()
    except Exception:
        d = {}
    return {"ok": True, "id": d.get("id", ""), "ts": d.get("time", time.time())}


def upload(filename: str, data: bytes, content_type: str = "") -> dict:
    """Ladda upp bild/fil (länken lever 24 h)."""
    files = {"fileToUpload": (filename or "fil", data, content_type or "application/octet-stream")}
    r = httpx.post(LITTERBOX, data={"reqtype": "fileupload", "time": "24h"},
                   files=files, timeout=90.0, follow_redirects=True)
    url = (r.text or "").strip()
    if r.status_code != 200 or not url.startswith("http"):
        raise RuntimeError(url[:200] or "uppladdning misslyckades")
    ct = content_type or ""
    low = url.lower()
    is_img = ct.startswith("image/") or low.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
    return {"url": url, "kind": "image" if is_img else "file"}
