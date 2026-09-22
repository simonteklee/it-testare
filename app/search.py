"""Webbsök (fas 3) — DuckDuckGo, filtrerat mot testkällor.

Resultat filtreras så att de håller sig till IT-test/kvalitet (vitlista + nyckelord).
"""
from __future__ import annotations

import html as _html
import re
import urllib.parse
from pathlib import Path

import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) IT-testare/0.1"}
WHITELIST_FILE = Path(__file__).resolve().parent.parent / "data" / "källor.yaml"

# Nyckelord som visar att ett resultat handlar om test/QA.
KEYWORDS = ["test", "testing", "tester", "qa", "kvalitet", "quality", "defect", "bug",
            "regression", "testfall", "testplan", "teststrategi", "automatis", "istqb",
            "acceptans", "verifier", "valider", "krav", "release", "scrum", "agil"]

DEFAULT_DOMAINS = [
    "wikipedia.org", "istqb.org", "ministryoftesting.com", "guru99.com",
    "softwaretestinghelp.com", "tutorialspoint.com", "browserstack.com",
    "testrail.com", "smartbear.com", "atlassian.com", "testingexcellence.com",
    "qameta.io", "swedq.se", "reqtest.com", "softwaretestingmagazine.com",
]


def _domains() -> list[str]:
    if WHITELIST_FILE.exists():
        try:
            import yaml
            data = yaml.safe_load(WHITELIST_FILE.read_text(encoding="utf-8")) or {}
            doms = data.get("domains") if isinstance(data, dict) else data
            if doms:
                return list(doms)
        except Exception:
            pass
    return DEFAULT_DOMAINS


def _decode(u: str) -> str:
    if u.startswith("//"):
        u = "https:" + u
    if "duckduckgo.com/l/" in u:
        qs = urllib.parse.urlparse(u).query
        u = urllib.parse.parse_qs(qs).get("uddg", [u])[0]
    return u


def _domain(u: str) -> str:
    try:
        return urllib.parse.urlparse(u).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _relevant(title: str, snippet: str, dom: str) -> bool:
    text = (title + " " + snippet).lower()
    if any(re.search(r"\b" + re.escape(k), text) for k in KEYWORDS):
        return True
    return any(d in dom for d in _domains())


def search(query: str, k: int = 5) -> list[dict]:
    q = query + " software testing QA"
    with httpx.Client(timeout=30.0, follow_redirects=True, headers=HEADERS) as c:
        r = c.post("https://html.duckduckgo.com/html/", data={"q": q})
        r.raise_for_status()
        page = r.text

    anchors = re.findall(r'result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.S)
    snippets = re.findall(r'result__snippet"[^>]*>(.*?)</a>', page, re.S)

    out = []
    for i, (href, title) in enumerate(anchors):
        url = _decode(href)
        dom = _domain(url)
        t = _html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        sn = snippets[i] if i < len(snippets) else ""
        sn = _html.unescape(re.sub(r"<[^>]+>", "", sn)).strip()
        if _relevant(t, sn, dom):
            out.append({"title": t, "url": url, "snippet": sn})
        if len(out) >= k:
            break
    return out
