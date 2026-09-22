"""Textextrahering ur många filtyper + chunkning + webbsidehämtning."""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import httpx

HEADERS = {"User-Agent": "IT-testare/0.1 (privat studieverktyg)"}

OFFICE_EXTS = {".docx", ".doc", ".odt", ".rtf", ".pptx", ".ppt", ".odp",
               ".xlsx", ".xls", ".ods", ".csv", ".txt"}
HTML_EXTS = {".html", ".htm", ".xhtml"}


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


def _soffice_to_text(path: Path) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["soffice", "--headless", "-env:UserInstallation=file:///tmp/loprofile-simi",
             "--convert-to", "txt:Text (encoded):UTF8", str(path), "--outdir", tmp],
            check=False, capture_output=True, timeout=120,
        )
        cands = list(Path(tmp).glob("*.txt"))
        if not cands:
            raise RuntimeError("kunde inte konvertera filen (soffice)")
        return cands[0].read_text(encoding="utf-8", errors="ignore")


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as t:
            out = t.name
        subprocess.run(["pdftotext", "-layout", str(path), out], check=True)
        return Path(out).read_text(encoding="utf-8", errors="ignore")
    if ext in HTML_EXTS:
        return html_to_text(path.read_text(encoding="utf-8", errors="ignore"))
    if ext in OFFICE_EXTS and ext not in {".txt", ".csv"}:
        return _soffice_to_text(path)
    # txt, csv, md, json, kod, m.m. → läs som text
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return _soffice_to_text(path)


def fetch_url(url: str) -> str:
    with httpx.Client(timeout=60.0, follow_redirects=True, headers=HEADERS) as c:
        r = c.get(url)
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        if "html" in ctype or url.lower().endswith((".html", ".htm")):
            return html_to_text(r.text)
        return r.text


def chunk(text: str, size: int = 900) -> list[str]:
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
