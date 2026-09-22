"""Kunskapsbas (RAG): embeddings via Gemini + lokal vektorlagring i JSONL.

Fas 2: hämta relevanta utdrag ur kunskapsbasen och skicka med som källor.
"""
from __future__ import annotations

import json
import math
import hashlib
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Lokala embeddings (gratis, ingen kvot, privat).
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
KB_FILE = DATA_DIR / "kb.jsonl"

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding(EMBED_MODEL)
    return _embedder


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeddar lokalt med fastembed (ingen extern kvot)."""
    m = _get_embedder()
    return [[float(x) for x in v] for v in m.embed(texts)]


def load() -> list[dict]:
    if not KB_FILE.exists():
        return []
    out = []
    for line in KB_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _h(text: str) -> str:
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:16]


def add_documents(docs: list[dict], batch: int = 50) -> int:
    """docs: [{text, source, url, kind}] → embeddar och lägger till. Hoppar över dubbletter."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    seen = {_h(d["text"]) for d in load()}
    fresh = []
    for d in docs:
        h = _h(d["text"])
        if h in seen:
            continue
        seen.add(h)
        fresh.append(d)
    added = 0
    with KB_FILE.open("a", encoding="utf-8") as f:
        for i in range(0, len(fresh), batch):
            part = fresh[i : i + batch]
            vecs = embed_texts([d["text"] for d in part])
            for d, v in zip(part, vecs):
                rec = {"text": d["text"], "source": d.get("source", ""),
                       "url": d.get("url", ""), "kind": d.get("kind", "kb"),
                       "h": _h(d["text"]), "vector": v}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                added += 1
    return added


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def search(query: str, k: int = 4) -> list[dict]:
    docs = load()
    if not docs:
        return []
    qv = embed_texts([query])[0]
    scored = [( _cos(qv, d["vector"]), d) for d in docs]
    scored.sort(key=lambda t: t[0], reverse=True)
    out = []
    for score, d in scored[:k]:
        out.append({"score": round(score, 4), "text": d["text"],
                    "source": d.get("source", ""), "url": d.get("url", ""),
                    "kind": d.get("kind", "kb")})
    return out


def count() -> int:
    return len(load())


def count_kind(kind: str) -> int:
    return sum(1 for d in load() if d.get("kind") == kind)
