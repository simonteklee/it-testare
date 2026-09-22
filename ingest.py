#!/usr/bin/env python3
"""Läs in källor i kunskapsbasen.

Exempel:
  .venv/bin/python ingest.py https://en.wikipedia.org/wiki/Software_testing
  .venv/bin/python ingest.py ~/Documents/.../kursplan.pdf
  .venv/bin/python ingest.py --reset https://...
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app import kb  # noqa: E402

HEADERS = {"User-Agent": "IT-testare/0.1 (privat studieverktyg)"}


def html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</(p|div|li|h[1-6]|tr)>", "\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    import html as _h
    text = _h.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def fetch_url(url: str) -> str:
    with httpx.Client(timeout=60.0, follow_redirects=True, headers=HEADERS) as c:
        r = c.get(url)
        r.raise_for_status()
        return html_to_text(r.text)


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as t:
            out = t.name
        subprocess.run(["pdftotext", "-layout", str(path), out], check=True)
        return Path(out).read_text(encoding="utf-8", errors="ignore")
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 1 <= size:
            cur = (cur + "\n" + p).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = p if len(p) <= size else p[:size]
    if cur:
        chunks.append(cur)
    return [c for c in chunks if len(c) > 60]


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args and args[0] == "--reset":
        kb.KB_FILE.unlink(missing_ok=True)
        print("Kunskapsbas rensad.")
        args = args[1:]

    total = 0
    for a in args:
        if a.startswith("http"):
            print(f"hämtar {a} …")
            text, src = fetch_url(a), a
        else:
            p = Path(a).expanduser()
            print(f"läser {p} …")
            text, src = read_file(p), p.name
        chunks = chunk(text)
        docs = [{"text": c, "source": src, "url": src if src.startswith("http") else ""} for c in chunks]
        n = kb.add_documents(docs)
        total += n
        print(f"  → {n} stycken inlästa")
    print(f"Klart. {total} nya stycken. Kunskapsbasen har nu {kb.count()} stycken.")


if __name__ == "__main__":
    main()
