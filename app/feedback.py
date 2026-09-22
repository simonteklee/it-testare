"""Kvalitetssäkring (fas 4): feedback, verifiering och granskningsläge.

- 👍/👎  → sparas i data/feedback.jsonl
- ✅ Verifiera → svaret blir ett betrott svar. I normalläge läggs det direkt i
  kunskapsbasen (källa "Verifierat svar"); i granskningsläge hamnar det i en kö
  (data/pending.jsonl) som du godkänner/avvisar.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(parents=True, exist_ok=True)
FEEDBACK = DATA / "feedback.jsonl"
PENDING = DATA / "pending.jsonl"
CONFIG = DATA / "config.json"


def _read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _append(p: Path, rec: dict) -> None:
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_config() -> dict:
    if CONFIG.exists():
        try:
            return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"review_mode": False}


def save_config(cfg: dict) -> None:
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def add_feedback(rec: dict) -> None:
    rec = {"ts": time.time(), **rec}
    _append(FEEDBACK, rec)


def _kb_add(text: str, source: str, url: str = "") -> int:
    from . import extract, kb
    docs = [{"text": c, "source": source, "url": url} for c in extract.chunk(text)]
    return kb.add_documents(docs)


def verify(rec: dict) -> dict:
    """Verifiera ett svar. Returnerar {status, kb_chunks?, pending?}"""
    add_feedback({**rec, "vote": "verify"})
    if load_config().get("review_mode"):
        _append(PENDING, {"ts": time.time(), **rec})
        return {"status": "pending", "pending": len(list_pending())}
    n = _kb_add(rec.get("answer", ""), "Verifierat svar")
    return {"status": "verified", "chunks": n, "kb_chunks": _kb_count()}


def list_pending() -> list[dict]:
    return _read_jsonl(PENDING)


def _write_pending(items: list[dict]) -> None:
    PENDING.write_text(
        "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), encoding="utf-8")


def approve(index: int) -> dict:
    items = list_pending()
    if index < 0 or index >= len(items):
        return {"error": "ogiltigt index"}
    item = items.pop(index)
    _write_pending(items)
    n = _kb_add(item.get("answer", ""), "Verifierat svar")
    return {"status": "approved", "chunks": n, "kb_chunks": _kb_count(), "pending": len(items)}


def reject(index: int) -> dict:
    items = list_pending()
    if index < 0 or index >= len(items):
        return {"error": "ogiltigt index"}
    items.pop(index)
    _write_pending(items)
    return {"status": "rejected", "pending": len(items)}


def _kb_count() -> int:
    from . import kb
    return kb.count()


def stats() -> dict:
    fb = _read_jsonl(FEEDBACK)
    return {
        "total": len(fb),
        "up": sum(1 for f in fb if f.get("vote") == "up"),
        "down": sum(1 for f in fb if f.get("vote") == "down"),
        "verified": sum(1 for f in fb if f.get("vote") == "verify"),
        "pending": len(list_pending()),
    }
