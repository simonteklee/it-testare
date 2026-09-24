"""Frågelogg & trender (lokalt).

- Varje fråga som ställs loggas lokalt i data/questions.jsonl.
- "Vad andra frågat" = de vanligaste frågorna (senaste listan).

Delning av frågor mellan användare sköts av `app/community.py` (via ntfy).
"""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(parents=True, exist_ok=True)
QUESTIONS = DATA / "questions.jsonl"


def log_question(q: str) -> None:
    q = (q or "").strip()
    if not q:
        return
    with QUESTIONS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "q": q}, ensure_ascii=False) + "\n")


def _read_jsonl(p: Path) -> list[dict]:
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


def top_questions(n: int = 10) -> list[dict]:
    c = Counter(r["q"] for r in _read_jsonl(QUESTIONS) if r.get("q"))
    return [{"q": q, "antal": k} for q, k in c.most_common(n)]
