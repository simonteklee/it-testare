"""Gemensam AI (community): alla som använder appen kan se och återanvända
varandras frågor OCH svar via en delad GitHub-gist.

- Lokala frågor+svar loggas i data/qa.jsonl.
- Vid synk: hämta gruppens Q&A, slå ihop (dedupe), spara lokalt och skicka tillbaka.
- Enklaste koppling: en enda inställning (på/av) mot en *förvald* gemensam gist.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from . import share

DATA = Path(__file__).resolve().parent.parent / "data"
QA_FILE = DATA / "qa.jsonl"
COMMUNITY_FILE = DATA / "community_qa.jsonl"
QA_NAME = "it-testare-qa.json"

# Alla app-installationer pekar som standard på samma gemensamma rum.
DEFAULT_GIST = "ba7f30550e6cf986010ecb5759ef4aa7"


def _h(s: str) -> str:
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()[:16]


def _key(q: str, a: str) -> str:
    return _h((q or "") + "||" + (a or ""))


def _read(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def log_qa(q: str, a: str, provider: str = "") -> None:
    q = (q or "").strip()
    a = (a or "").strip()
    if not q or not a:
        return
    DATA.mkdir(parents=True, exist_ok=True)
    with QA_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"q": q, "a": a, "provider": provider, "ts": time.time()},
                           ensure_ascii=False) + "\n")


def _norm(recs: list[dict]) -> list[dict]:
    out = []
    for r in recs or []:
        if not r.get("a"):
            continue
        out.append({"q": r.get("q", ""), "a": r.get("a", ""),
                    "provider": r.get("provider", ""), "ts": r.get("ts", 0)})
    return out


def merge(*lists) -> list[dict]:
    seen, out = set(), []
    for lst in lists:
        for r in _norm(lst):
            k = _key(r["q"], r["a"])
            if k in seen:
                continue
            seen.add(k)
            out.append(r)
    return out


def all_qa() -> list[dict]:
    """Lokala + hämtade (för visning i UI)."""
    out = merge(_read(COMMUNITY_FILE), _read(QA_FILE))
    out.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return out


def count() -> int:
    return len(all_qa())


def pull_push(gist_id: str) -> dict:
    remote: list[dict] = []
    try:
        g = share.get_gist(gist_id)
        for fn, f in g.get("files", {}).items():
            if fn.endswith(".json"):
                try:
                    obj = json.loads(f["content"])
                    remote = obj.get("qa", []) if isinstance(obj, dict) else obj
                except Exception:
                    pass
    except Exception:
        remote = []
    merged = merge(remote, _read(QA_FILE))
    COMMUNITY_FILE.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in merged), encoding="utf-8")
    blocked = False
    try:
        share.put_file(gist_id, QA_NAME,
                       json.dumps({"qa": merged}, ensure_ascii=False),
                       "IT-testare - delad Q&A")
    except Exception:
        blocked = True
    return {"remote": len(remote), "total": len(merged), "pushed": not blocked}
