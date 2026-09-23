"""Delning & community (fas 5): frågelogg, "vad andra sökt", delningspaket, GitHub Gist.

- Frågor loggas lokalt → "vad andra sökt" (vanligaste frågorna).
- Ett *delningspaket* innehåller verifierade svar + vanliga frågor.
- Paketet kan laddas ner/sparas, eller publiceras/hämtas som en (hemlig) GitHub Gist,
  så du och en vän kan lära av varandra.
"""
from __future__ import annotations

import json
import hashlib
import subprocess
import time
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(parents=True, exist_ok=True)
QUESTIONS = DATA / "questions.jsonl"
FEEDBACK = DATA / "feedback.jsonl"
CONFIG = DATA / "config.json"
PACK_VERSION = 1


def log_question(q: str) -> None:
    q = (q or "").strip()
    if not q:
        return
    with QUESTIONS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "q": q}, ensure_ascii=False) + "\n")


def _read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def top_questions(n: int = 10) -> list[dict]:
    c = Counter(r["q"] for r in _read_jsonl(QUESTIONS) if r.get("q"))
    return [{"q": q, "antal": k} for q, k in c.most_common(n)]


def _verified() -> list[dict]:
    out = []
    for f in _read_jsonl(FEEDBACK):
        if f.get("vote") == "verify" and f.get("answer"):
            out.append({"question": f.get("question", ""), "answer": f.get("answer", "")})
    return out


def build_pack(kind: str = "tips") -> dict:
    return {
        "version": PACK_VERSION,
        "kind": kind,  # "tips" = bara frågor/vanligast, "svar" = inkl. verifierade svar
        "created": time.time(),
        "verified": _verified(),
        "top_questions": top_questions(20),
    }


def import_pack(pack: dict) -> dict:
    """Lägg in andras verifierade svar i kunskapsbasen (märkta som community)."""
    from . import kb
    docs = []
    for v in pack.get("verified", []):
        ans = (v.get("answer") or "").strip()
        if len(ans) < 40:
            continue
        docs.append({"text": ans, "source": "Community-svar", "url": "", "kind": "community"})
    n = kb.add_documents(docs) if docs else 0
    return {"added": n, "kb_chunks": kb.count(), "community": kb.count_kind("community")}


def _vkey(v: dict) -> str:
    s = (v.get("question", "") + "||" + v.get("answer", "")).encode("utf-8")
    return hashlib.sha1(s).hexdigest()[:16]


def merge_verified(*lists) -> list[dict]:
    seen, out = set(), []
    for lst in lists:
        for v in (lst or []):
            k = _vkey(v)
            if k in seen:
                continue
            seen.add(k)
            out.append({"question": v.get("question", ""), "answer": v.get("answer", "")})
    return out


def sync(gist_id: str) -> dict:
    """Tvåvägssynk mot en delad gist: hämta → slå ihop med lokala → lägg in → putta tillbaka."""
    try:
        remote = fetch_gist(gist_id)
    except Exception:
        remote = {"verified": []}
    local = build_pack("svar")
    merged = merge_verified(remote.get("verified", []), local.get("verified", []))
    res = import_pack({"verified": merged})
    try:
        pushed = publish_gist({"version": PACK_VERSION, "kind": "svar", "created": time.time(),
                               "verified": merged, "top_questions": local.get("top_questions", [])},
                              gist_id)
    except Exception as e:  # noqa: BLE001
        pushed = {"error": str(e)}
    return {"pulled": len(remote.get("verified", [])), "merged": len(merged),
            "pushed": pushed, **res}


# ---- GitHub Gist (gratis, använder din gh-inloggning) ----

def _token() -> str | None:
    import os
    if os.getenv("GH_TOKEN"):
        return os.getenv("GH_TOKEN")
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                              timeout=10).stdout.strip() or None
    except Exception:
        return None


def _gist_headers() -> dict:
    t = _token()
    if not t:
        raise RuntimeError("Ingen GitHub-token (kör 'gh auth login').")
    return {"Authorization": f"Bearer {t}", "Accept": "application/vnd.github+json"}


def publish_gist(pack: dict, gist_id: str | None = None) -> dict:
    import httpx
    payload = {
        "description": "TestARN – delat kunskapspaket",
        "public": False,
        "files": {"it-testare-paket.json": {"content": json.dumps(pack, ensure_ascii=False, indent=2)}},
    }
    with httpx.Client(timeout=30.0) as c:
        if gist_id:
            r = c.patch(f"https://api.github.com/gists/{gist_id}", headers=_gist_headers(), json=payload)
        else:
            r = c.post("https://api.github.com/gists", headers=_gist_headers(), json=payload)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"gist {r.status_code}: {r.text[:200]}")
        d = r.json()
    return {"id": d["id"], "url": d["html_url"]}


def fetch_gist(gist_id: str) -> dict:
    import httpx
    with httpx.Client(timeout=30.0) as c:
        r = c.get(f"https://api.github.com/gists/{gist_id}", headers=_gist_headers())
        if r.status_code != 200:
            raise RuntimeError(f"gist {r.status_code}")
        d = r.json()
    for fn, f in d.get("files", {}).items():
        if fn.endswith(".json"):
            return json.loads(f["content"])
    raise RuntimeError("ingen json-fil i gisten")


def get_gist(gist_id: str) -> dict:
    """Hämta hela gisten (metadata + alla filer)."""
    import httpx
    with httpx.Client(timeout=30.0) as c:
        r = c.get(f"https://api.github.com/gists/{gist_id}", headers=_gist_headers())
        if r.status_code != 200:
            raise RuntimeError(f"gist {r.status_code}")
        return r.json()


def put_file(gist_id: str, filename: str, content: str, description: str = "TestARN") -> dict:
    """Skriv/uppdatera en fil i en gist."""
    import httpx
    with httpx.Client(timeout=60.0) as c:
        r = c.patch(f"https://api.github.com/gists/{gist_id}", headers=_gist_headers(),
                    json={"description": description,
                          "files": {filename: {"content": content}}})
        if r.status_code not in (200, 201):
            raise RuntimeError(f"gist {r.status_code}: {r.text[:200]}")
        return r.json()
