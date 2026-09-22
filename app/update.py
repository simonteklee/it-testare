"""Uppdatering (fas 6): hämta senaste versionen från GitHub och uppdatera appen.

- Kollar senaste version via `version.txt` i repot.
- Uppdaterar: `git pull` om appen är en git-klon, annars laddar tarball och kopierar koden
  (behåller `.env`, `data/` och `.venv`).
- Startar om tjänsten (systemd på Linux; på Windows ombeds användaren starta om).
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import tarfile
import tempfile
import threading
import time
from pathlib import Path

import httpx

from . import __version__

ROOT = Path(__file__).resolve().parent.parent
REPO = "simonteklee/it-testare"
BRANCH = "main"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
TARBALL = f"https://codeload.github.com/{REPO}/tar.gz/refs/heads/{BRANCH}"
KEEP = {".env", "data", ".venv", "dist", ".git"}


def latest_version() -> str:
    # 1) GitHub API (färskt, ej CDN-cachat)
    try:
        from . import share
        headers = {}
        try:
            headers.update(share._gist_headers())
        except Exception:
            pass
        headers["Accept"] = "application/vnd.github.raw"
        r = httpx.get(f"https://api.github.com/repos/{REPO}/contents/version.txt",
                      headers=headers, timeout=15.0, follow_redirects=True)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
    except Exception:
        pass
    # 2) raw (kan vara cachat nagon minut)
    try:
        import time as _t
        r = httpx.get(f"{RAW}/version.txt?t={int(_t.time())}", timeout=15.0, follow_redirects=True)
        if r.status_code == 200:
            return r.text.strip()
    except Exception:
        pass
    return ""


def status() -> dict:
    lv = latest_version()
    return {"current": __version__, "latest": lv or __version__,
            "update_available": bool(lv) and lv != __version__}


def _apply_git() -> dict:
    p = subprocess.run(["git", "-C", str(ROOT), "pull", "--ff-only"],
                       capture_output=True, text=True)
    return {"ok": p.returncode == 0, "method": "git", "output": (p.stdout + p.stderr)[-400:]}


def _apply_tarball() -> dict:
    with httpx.stream("GET", TARBALL, timeout=180.0, follow_redirects=True) as r:
        r.raise_for_status()
        data = b"".join(r.iter_bytes())
    tmp = Path(tempfile.mkdtemp())
    try:
        with tarfile.open(fileobj=io.BytesIO(data)) as tf:
            tf.extractall(tmp)
        inner = next(p for p in tmp.iterdir() if p.is_dir())
        for item in inner.iterdir():
            if item.name in KEEP:
                continue
            dest = ROOT / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {"ok": True, "method": "tarball"}


def apply() -> dict:
    if (ROOT / ".git").exists():
        res = _apply_git()
        if res.get("ok"):
            return res
    return _apply_tarball()


def _restart_later() -> None:
    time.sleep(1.5)
    try:
        if os.name == "nt":
            ps = ("Start-Sleep 2; Get-Process uvicorn -ErrorAction SilentlyContinue | "
                  f"Stop-Process -Force; Start-Process '{ROOT}\\start.vbs'")
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps])
        else:
            subprocess.Popen(["systemctl", "--user", "restart", "it-testare.service"])
    except Exception:
        pass


def update_and_restart() -> dict:
    res = apply()
    try:  # läs in nya versionen
        res["new_version"] = (ROOT / "version.txt").read_text(encoding="utf-8").strip()
    except Exception:
        res["new_version"] = ""
    # starta om strax efter att svaret skickats
    unit = Path.home() / ".config" / "systemd" / "user" / "it-testare.service"
    can_auto = os.name == "nt" or (unit.exists() and shutil.which("systemctl") is not None)
    if res.get("ok") and can_auto:
        threading.Thread(target=_restart_later, daemon=True).start()
        res["restart"] = "auto"
    else:
        res["restart"] = "manual"
    return res
