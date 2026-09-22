"""IT-testare — FastAPI-backend (Fas 3: RAG + webbsök + källor + filuppladdning)."""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import extract, feedback, kb, search, share
from .llm import ProviderError, available_providers, generate

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
UPLOAD_DIR = ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="IT-testare", version="0.3.0")
app.mount("/vendor", StaticFiles(directory=WEB_DIR / "vendor"), name="vendor")
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    web: bool = True


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
    shared_gist: str | None = None


class ImportRequest(BaseModel):
    pack: dict | None = None


class GistRequest(BaseModel):
    gist_id: str = ""


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
    return {"status": "ok", "app": "IT-testare",
            "providers": available_providers(), "kb_chunks": kb.count(),
            "community": kb.count_kind("community"),
            "qa": feedback.stats(), "review_mode": feedback.load_config().get("review_mode", False),
            "shared_gist": feedback.load_config().get("shared_gist", "")}


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
        return JSONResponse({**result, "sources": sources})
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
    if req.shared_gist is not None:
        gid = req.shared_gist.strip()
        if gid and "/" in gid:
            gid = gid.rstrip("/").split("/")[-1]
        cfg["shared_gist"] = gid
    feedback.save_config(cfg)
    return cfg


@app.post("/api/sync")
async def api_sync() -> JSONResponse:
    gid = feedback.load_config().get("shared_gist", "")
    if not gid:
        return JSONResponse({"error": "Ingen delad bas vald."}, status_code=400)
    try:
        return JSONResponse(share.sync(gid))
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


@app.get("/api/export")
async def export_pack() -> JSONResponse:
    return JSONResponse(share.build_pack("svar"))


@app.post("/api/import")
async def import_pack(req: ImportRequest) -> JSONResponse:
    if not req.pack:
        return JSONResponse({"error": "inget paket"}, status_code=400)
    return JSONResponse(share.import_pack(req.pack))


@app.post("/api/share/gist")
async def share_gist(req: GistRequest) -> JSONResponse:
    try:
        return JSONResponse(share.publish_gist(share.build_pack("svar"), req.gist_id or None))
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=400)


@app.post("/api/fetch/gist")
async def fetch_gist(req: GistRequest) -> JSONResponse:
    try:
        pack = share.fetch_gist(req.gist_id)
        return JSONResponse({**share.import_pack(pack), "from_gist": req.gist_id})
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html, headers={"Cache-Control": "no-store, max-age=0"})
