"""Avinstallera / återställ — stoppa appen och radera appmappen + genvägar.

Anropas från den dolda knappen i appen ("💡 tips & dela" → 🗑). Så att en annan
webbsida inte kan radera appen via localhost krävs BÅDE en engångstoken (slumpas
per serverstart) OCH att man skriver RADERA.

Efteråt kan man köra installationsraden igen och få en helt färsk app.
"""
from __future__ import annotations

import os
import secrets
import subprocess
import tempfile
import threading
import time
from pathlib import Path

APPDIR = Path(__file__).resolve().parent.parent
TOKEN = secrets.token_urlsafe(24)


def app_dir() -> str:
    return str(APPDIR)


def platform_name() -> str:
    return "windows" if os.name == "nt" else "posix"


def script_text() -> tuple[str, str]:
    """Bygger (sökväg, innehåll) för städskriptet. Rör inget på disk."""
    if os.name == "nt":
        home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        desktop = os.path.join(home, "Desktop")
        startmenu = os.path.join(os.environ.get("APPDATA", ""),
                                 "Microsoft", "Windows", "Start Menu", "Programs")
        text = (
            "@echo off\r\n"
            "timeout /t 2 /nobreak >nul\r\n"
            "taskkill /f /im uvicorn.exe >nul 2>&1\r\n"
            "rmdir /s /q \"" + str(APPDIR) + "\"\r\n"
            "del \"" + desktop + "\\TestARN.lnk\" >nul 2>&1\r\n"
            "del \"" + startmenu + "\\TestARN.lnk\" >nul 2>&1\r\n"
            "del \"%~f0\"\r\n"
        )
        return os.path.join(tempfile.gettempdir(), "testarn-uninstall.cmd"), text

    text = (
        "#!/usr/bin/env bash\n"
        "systemctl --user stop testarn.service 2>/dev/null\n"
        "systemctl --user disable testarn.service 2>/dev/null\n"
        "rm -f \"$HOME/.config/systemd/user/testarn.service\"\n"
        "systemctl --user daemon-reload 2>/dev/null\n"
        "pkill -f 'uvicorn app[.]main:app' 2>/dev/null\n"
        "sleep 1\n"
        "rm -rf \"" + str(APPDIR) + "\"\n"
        "rm -f \"$HOME/.local/share/applications/testarn.desktop\" \"$HOME/Desktop/testarn.desktop\"\n"
        "rm -f \"$0\"\n"
    )
    return os.path.join(tempfile.gettempdir(), "testarn-uninstall.sh"), text


def _launch(path: str) -> None:
    if os.name == "nt":
        detached = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(["cmd", "/c", path], creationflags=detached, close_fds=True)
    else:
        os.chmod(path, 0o755)
        subprocess.Popen(["bash", path], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)


def _schedule_exit(delay: float = 1.5) -> None:
    """Stäng av servern strax efter att svaret skickats, så att mappen kan raderas."""
    def bye() -> None:
        time.sleep(delay)
        os._exit(0)
    threading.Thread(target=bye, daemon=True).start()


def uninstall(token: str, confirm: str) -> dict:
    if (confirm or "").strip().upper() != "RADERA":
        raise ValueError("skriv RADERA for att bekrafta")
    if not token or token != TOKEN:
        raise ValueError("ogiltig token")
    path, text = script_text()
    Path(path).write_text(text, encoding="utf-8")
    _launch(path)
    _schedule_exit()
    return {"ok": True, "removing": str(APPDIR), "script": path,
            "hint": "Klart. TestARN stangs och raderas. Kor installationsraden igen for en farsk app."}
