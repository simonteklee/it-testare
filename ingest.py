#!/usr/bin/env python3
"""Läs in källor i kunskapsbasen (kommandoraden).

Exempel:
  .venv/bin/python ingest.py https://en.wikipedia.org/wiki/Software_testing
  .venv/bin/python ingest.py ~/Documents/rapport.pdf ~/anteckningar.md
  .venv/bin/python ingest.py --reset https://...
Stödjer pdf, docx/odt/pptx/xlsx (via LibreOffice), html, txt, md, csv, json m.m.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app import extract, kb  # noqa: E402


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
            text, src = extract.fetch_url(a), a
        else:
            p = Path(a).expanduser()
            print(f"läser {p} …")
            text, src = extract.extract_text(p), p.name
        chunks = extract.chunk(text)
        docs = [{"text": c, "source": src, "url": src if src.startswith("http") else ""}
                for c in chunks]
        n = kb.add_documents(docs)
        total += n
        print(f"  → {n} stycken inlästa")
    print(f"Klart. {total} nya stycken. Kunskapsbasen har nu {kb.count()} stycken.")


if __name__ == "__main__":
    main()
