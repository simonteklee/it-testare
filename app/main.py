"""TestARN — FastAPI-backend (Fas 3: RAG + webbsök + källor + filuppladdning)."""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import community, extract, feedback, kb, reset, search, share, update
from . import chat as chat_mod
from .llm import ProviderError, available_providers, generate

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
UPLOAD_DIR = ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="TestARN", version="0.3.0")
app.mount("/vendor", StaticFiles(directory=WEB_DIR / "vendor"), name="vendor")
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    web: bool = True
    thread: str = ""
    parent: str = ""


class UrlRequest(BaseModel):
    url: str


class FeedbackRequest(BaseModel):
    question: str = ""
    answer: str = ""
    provider: str = ""
    model: str = ""
    vote: str = ""
    comment: str = ""


class VerifyRequest(BaseModel):
    question: str = ""
    answer: str = ""
    provider: str = ""
    model: str = ""


class ConfigRequest(BaseModel):
    review_mode: bool | None = None
    chat_on: bool | None = None
    chat_name: str | None = None
    chat_topic: str | None = None


class ChatSendRequest(BaseModel):
    text: str = ""
    name: str = ""
    url: str = ""
    kind: str = ""


class UninstallRequest(BaseModel):
    token: str = ""
    confirm: str = ""


class CommunityRequest(BaseModel):
    on: bool | None = None
    topic: str | None = None


def gather(query: str, use_web: bool) -> tuple[str, list[dict]]:
    """Samlar kontext + källor från kunskapsbas och (valfritt) webbsök."""
    parts: list[str] = []
    sources: list[dict] = []
    n = 0

    try:
        hits = kb.search(query, k=4) if kb.count() else []
    except Exception:
        hits = []
    for h in hits:
        n += 1
        parts.append(f"[{n}] ({h['source']})\n{h['text']}")
        sources.append({"n": n, "source": h["source"], "url": h.get("url", ""),
                         "score": h.get("score"), "kind": h.get("kind", "kb")})

    if use_web:
        try:
            results = search.search(query, k=4)
        except Exception:
            results = []
        for i, w in enumerate(results):
            n += 1
            body = w["snippet"]
            if i < 2:  # hämta mer text från de två första träffarna
                try:
                    full = extract.fetch_url(w["url"])
                    body = (full[:1800] + " …") if full else body
                except Exception:
                    pass
            parts.append(f"[{n}] ({w['title']} — {w['url']})\n{body}")
            sources.append({"n": n, "source": w["title"] or w["url"],
                             "url": w["url"], "kind": "web"})
    return "\n\n".join(parts), sources


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "app": "TestARN",
            "providers": available_providers(), "kb_chunks": kb.count(),
            "community": kb.count_kind("community"),
            "qa": feedback.stats(), "review_mode": feedback.load_config().get("review_mode", False),
            "community_on": feedback.load_config().get("community_on", True),
            "community_topic": community.topic(),
            "community_count": community.count()}


@app.post("/api/chat")
async def chat(req: ChatRequest) -> JSONResponse:
    msgs = [m.model_dump() for m in req.messages if m.content.strip()]
    if not msgs:
        return JSONResponse({"error": "Tom fråga"}, status_code=400)
    last_user = next((m["content"] for m in reversed(msgs) if m["role"] == "user"), "")
    share.log_question(last_user)
    context, sources = gather(last_user, req.web)
    try:
        result = await generate(msgs, context=context or None)
        qa_id = ""
        try:
            qa_id = community.log_qa(last_user, result.get("answer", ""),
                                     result.get("provider", ""), req.thread, req.parent)
        except Exception:
            pass
        return JSONResponse({**result, "sources": sources, "qa_id": qa_id})
    except ProviderError as e:
        return JSONResponse({"error": str(e)}, status_code=502)


def _ingest_text(text: str, source: str, url: str = "") -> int:
    docs = [{"text": c, "source": source, "url": url} for c in extract.chunk(text)]
    return kb.add_documents(docs)


@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)) -> dict:
    results = []
    for f in files:
        name = Path(f.filename or "fil").name
        dest = UPLOAD_DIR / name
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)
        try:
            n = _ingest_text(extract.extract_text(dest), name, f"/files/{name}")
            results.append({"file": name, "chunks": n})
        except Exception as e:  # noqa: BLE001
            results.append({"file": name, "error": str(e)})
    return {"results": results, "kb_chunks": kb.count()}


@app.post("/api/ingest-url")
async def ingest_url(req: UrlRequest) -> dict:
    try:
        n = _ingest_text(extract.fetch_url(req.url), req.url, req.url)
        return {"url": req.url, "chunks": n, "kb_chunks": kb.count()}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/api/config")
async def get_config() -> dict:
    return feedback.load_config()


@app.post("/api/config")
async def set_config(req: ConfigRequest) -> dict:
    cfg = feedback.load_config()
    if req.review_mode is not None:
        cfg["review_mode"] = req.review_mode
    if req.chat_on is not None:
        cfg["chat_on"] = req.chat_on
    if req.chat_name is not None:
        cfg["chat_name"] = req.chat_name.strip()[:40]
    if req.chat_topic is not None:
        cfg["chat_topic"] = req.chat_topic.strip()[:64]
    feedback.save_config(cfg)
    return cfg


@app.get("/api/classchat")
async def classchat_list() -> dict:
    return {"on": chat_mod.enabled(), "topic": chat_mod.topic(), "name": chat_mod.my_name(),
            "messages": chat_mod.fetch()}


@app.post("/api/classchat")
async def classchat_send(req: ChatSendRequest) -> JSONResponse:
    try:
        res = chat_mod.send(req.text, req.name, req.url, req.kind)
        return JSONResponse({**res, "name": chat_mod.my_name(), "messages": chat_mod.fetch()})
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=400)


@app.post("/api/classchat/upload")
async def classchat_upload(file: UploadFile = File(...)) -> JSONResponse:
    data = await file.read()
    if len(data) > 15 * 1024 * 1024:
        return JSONResponse({"error": "Filen är för stor (max 15 MB)."}, status_code=400)
    try:
        return JSONResponse(chat_mod.upload(file.filename or "fil", data, file.content_type or ""))
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=400)


@app.post("/api/feedback")
async def api_feedback(req: FeedbackRequest) -> dict:
    feedback.add_feedback(req.model_dump())
    return {"ok": True, "qa": feedback.stats()}


@app.post("/api/verify")
async def api_verify(req: VerifyRequest) -> dict:
    res = feedback.verify(req.model_dump())
    return {**res, "qa": feedback.stats()}


@app.get("/api/pending")
async def api_pending() -> dict:
    return {"items": feedback.list_pending()}


@app.post("/api/pending/{index}/approve")
async def api_approve(index: int) -> dict:
    return feedback.approve(index)


@app.post("/api/pending/{index}/reject")
async def api_reject(index: int) -> dict:
    return feedback.reject(index)


@app.get("/api/trending")
async def trending() -> dict:
    return {"top": share.top_questions(12)}


@app.get("/manifest.webmanifest")
async def manifest() -> FileResponse:
    return FileResponse(WEB_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js")
async def service_worker() -> FileResponse:
    return FileResponse(WEB_DIR / "sw.js", media_type="application/javascript")


@app.get("/icon-192.png")
async def icon192() -> FileResponse:
    return FileResponse(WEB_DIR / "icon-192.png", media_type="image/png")


@app.get("/icon-512.png")
async def icon512() -> FileResponse:
    return FileResponse(WEB_DIR / "icon-512.png", media_type="image/png")


@app.get("/api/community")
async def community_status() -> dict:
    cfg = feedback.load_config()
    return {"on": cfg.get("community_on", True),
            "topic": community.topic(),
            "count": community.count(),
            "default_topic": community.DEFAULT_TOPIC}


@app.post("/api/community")
async def community_set(req: CommunityRequest) -> dict:
    cfg = feedback.load_config()
    if req.on is not None:
        cfg["community_on"] = req.on
    if req.topic is not None:
        cfg["qa_topic"] = req.topic.strip() or community.DEFAULT_TOPIC
    feedback.save_config(cfg)
    return cfg


@app.post("/api/community/sync")
async def community_sync() -> JSONResponse:
    try:
        return JSONResponse(community.sync())
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/api/community/list")
async def community_list() -> dict:
    return {"items": community.all_qa()[:60]}


@app.get("/api/version")
async def version_info() -> dict:
    return update.status()


@app.post("/api/update")
async def do_update() -> JSONResponse:
    try:
        return JSONResponse(update.update_and_restart())
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/api/uninstall")
async def uninstall_info() -> dict:
    return {"token": reset.TOKEN, "dir": reset.app_dir(), "platform": reset.platform_name()}


@app.post("/api/uninstall")
async def do_uninstall(req: UninstallRequest) -> JSONResponse:
    try:
        return JSONResponse(reset.uninstall(req.token, req.confirm))
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html, headers={"Cache-Control": "no-store, max-age=0"})
