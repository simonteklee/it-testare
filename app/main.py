"""IT-testare — FastAPI-backend (Fas 2: RAG + källor)."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import kb
from .llm import ProviderError, available_providers, generate

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="IT-testare", version="0.2.0")
app.mount("/vendor", StaticFiles(directory=WEB_DIR / "vendor"), name="vendor")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


def _build_context(hits: list[dict]) -> tuple[str, list[dict]]:
    if not hits:
        return "", []
    ctx_lines, sources = [], []
    for i, h in enumerate(hits, 1):
        ctx_lines.append(f"[{i}] ({h['source']})\n{h['text']}")
        sources.append({"n": i, "source": h["source"], "url": h.get("url", ""),
                         "score": h.get("score")})
    return "\n\n".join(ctx_lines), sources


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "app": "IT-testare",
            "providers": available_providers(), "kb_chunks": kb.count()}


@app.post("/api/chat")
async def chat(req: ChatRequest) -> JSONResponse:
    msgs = [m.model_dump() for m in req.messages if m.content.strip()]
    if not msgs:
        return JSONResponse({"error": "Tom fråga"}, status_code=400)
    last_user = next((m["content"] for m in reversed(msgs) if m["role"] == "user"), "")
    # Hämta relevanta utdrag ur kunskapsbasen (RAG)
    try:
        hits = kb.search(last_user, k=4) if kb.count() else []
    except Exception:
        hits = []
    context, sources = _build_context(hits)
    try:
        result = await generate(msgs, context=context or None)
        return JSONResponse({**result, "sources": sources})
    except ProviderError as e:
        return JSONResponse({"error": str(e)}, status_code=502)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")
