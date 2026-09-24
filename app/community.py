"""Klassens frågor (community): alla som använder appen ser varandras frågor.

Ingen inloggning, inga nycklar. Frågorna delas via **ntfy.sh** (gratis, inget konto)
på samma sätt som klasschatten:

- Varje fråga+svar publiceras som ett litet JSON-meddelande till en gemensam *topic*.
- Appen pollar topicen, slår ihop med sina egna frågor (dedupe på frågetexten) och
  visar allt under "Klassens frågor".
- Allt ligger kvar lokalt i data/community_qa.jsonl så att listan finns även när
  ntfy:s cache (ca 12 h) har rensat gamla meddelanden.

Ingen hemlighet i topic-namnet, men ett svårgissat namn så att inte vem som helst
råkar hitta in.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import httpx

from . import feedback

DATA = Path(__file__).resolve().parent.parent / "data"
QA_FILE = DATA / "qa.jsonl"
COMMUNITY_FILE = DATA / "community_qa.jsonl"
PUSHED_FILE = DATA / "qa_pushed.json"

NTFY = "https://ntfy.sh"
# Gemensamt klassrum för frågor. Alla installationer pekar som standard hit, så att
# allas frågor syns hos alla utan att någon behöver klistra in en nyckel eller ett id.
DEFAULT_TOPIC = "testarn-fragor-7b3d91c4"

# ntfy tål stora meddelanden; skydda ändå mot orimliga svar.
MAX_BODY = 60000


def _cfg() -> dict:
    return feedback.load_config()


def topic() -> str:
    return (_cfg().get("qa_topic") or DEFAULT_TOPIC).strip() or DEFAULT_TOPIC


def enabled() -> bool:
    return bool(_cfg().get("community_on", True))


def _my_name() -> str:
    """Vem ställer frågan (samma namn som i klasschatten)."""
    try:
        from . import chat
        return chat.my_name()
    except Exception:
        return "Anonym"


def _h(s: str) -> str:
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()[:16]


def _key(q: str) -> str:
    """Dedupe-nyckel: en post per unik frågetext (så att samma fråga inte dubbeltas)."""
    return _h((q or "").strip().lower())


def _read(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def log_qa(q: str, a: str, provider: str = "", thread: str = "", parent: str = "") -> str:
    """Loggar ett fråga/svar lokalt. thread+parent gör att följdfrågor kan grupperas
    ihop med sin ursprungsfråga i UI:t. Returnerar postens id."""
    q = (q or "").strip()
    a = (a or "").strip()
    if not q or not a:
        return ""
    DATA.mkdir(parents=True, exist_ok=True)
    rec = {"q": q, "a": a, "provider": provider, "ts": time.time()}
    if thread:
        rec["thread"] = thread
    if parent:
        rec["parent"] = parent
    with QA_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return _key(q)


def _norm(recs: list[dict]) -> list[dict]:
    out = []
    for r in recs or []:
        if not isinstance(r, dict) or not r.get("a"):
            continue
        rec = {"q": r.get("q", ""), "a": r.get("a", ""),
               "provider": r.get("provider", ""), "ts": r.get("ts", 0)}
        if r.get("src"):
            rec["src"] = str(r["src"])[:40]
        if r.get("thread"):
            rec["thread"] = r["thread"]
        if r.get("parent"):
            rec["parent"] = r["parent"]
        rec["id"] = _key(rec["q"])
        out.append(rec)
    return out


def merge(*lists) -> list[dict]:
    seen, out = set(), []
    for lst in lists:
        for r in _norm(lst):
            k = _key(r["q"])
            if k in seen:
                continue
            seen.add(k)
            out.append(r)
    return out


def all_qa() -> list[dict]:
    """Lokala + hämtade (för visning i UI). Lokala först så att thread/parent
    (följdfrågor) bevaras om samma fråga finns i gruppen."""
    out = merge(_read(QA_FILE), _read(COMMUNITY_FILE))
    out.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return out


def count() -> int:
    return len(all_qa())


# ---- ntfy: dela & hämta ----

def _pushed() -> set[str]:
    try:
        return set(json.loads(PUSHED_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _save_pushed(ids: set[str]) -> None:
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        PUSHED_FILE.write_text(json.dumps(sorted(ids)), encoding="utf-8")
    except Exception:
        pass


def _post(rec: dict) -> dict:
    payload = {"q": rec.get("q", ""), "a": rec.get("a", ""),
               "ts": rec.get("ts", time.time()), "src": _my_name()}
    for k in ("thread", "parent"):
        if rec.get(k):
            payload[k] = rec[k]
    body = json.dumps(payload, ensure_ascii=False)
    if len(body.encode("utf-8")) > MAX_BODY:  # kapa svaret så att det ryms
        keep = MAX_BODY - (len(body) - len(rec.get("a", "") or "")) - 64
        payload["a"] = (rec.get("a", "") or "")[:max(0, keep)]
        body = json.dumps(payload, ensure_ascii=False)
    r = httpx.post(f"{NTFY}/{topic()}", content=body.encode("utf-8"),
                   headers={"Content-Type": "text/plain; charset=utf-8"},
                   timeout=20.0, follow_redirects=True)
    if r.status_code != 200:
        raise RuntimeError(f"ntfy {r.status_code}: {r.text[:160]}")
    try:
        d = r.json()
    except Exception:
        d = {}
    return {"ok": True, "id": d.get("id", ""), "ts": d.get("time", time.time())}


def fetch_remote() -> list[dict]:
    """Hämta klassens frågor från ntfy (cachen räcker ca 12 h)."""
    out: list[dict] = []
    try:
        r = httpx.get(f"{NTFY}/{topic()}/json",
                      params={"poll": "1", "since": "24h"},
                      timeout=15.0, follow_redirects=True)
        if r.status_code == 200:
            for line in r.text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                if o.get("event") != "message":
                    continue
                try:
                    rec = json.loads(o.get("message", ""))
                except Exception:
                    continue
                if not isinstance(rec, dict) or not rec.get("q"):
                    continue
                rec.setdefault("ts", o.get("time", 0))
                out.append(rec)
    except Exception:
        pass
    return out


def _migrate_pushed() -> set[str]:
    """Första gången: markera redan befintliga lokala frågor som delade, så att
    gammal historik inte publiceras retroaktivt."""
    pushed = _pushed()
    if not pushed and not PUSHED_FILE.exists():
        pushed = {_key(r.get("q", "")) for r in _read(QA_FILE) + _read(COMMUNITY_FILE)
                  if r.get("q")}
        _save_pushed(pushed)
    return pushed


def sync() -> dict:
    """Hämta allas frågor, slå ihop med lokala, och publicera nya lokala frågor."""
    remote = fetch_remote()
    merged = merge(remote, _read(QA_FILE))
    try:
        COMMUNITY_FILE.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in merged), encoding="utf-8")
    except Exception:
        pass

    pushed = _migrate_pushed()
    posted = failed = 0
    if enabled():
        for rec in _read(QA_FILE):
            k = _key(rec.get("q", ""))
            if not k or k in pushed:
                continue
            try:
                _post(rec)
                pushed.add(k)
                posted += 1
            except Exception:
                failed += 1
        _save_pushed(pushed)

    return {"remote": len(remote), "total": len(merged), "posted": posted,
            "failed": failed, "topic": topic()}

