"""IT-testare — FastAPI-backend (Fas 1: MVP-chatt)."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from .llm import ProviderError, available_providers, generate

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="IT-testare", version="0.1.0")


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "app": "IT-testare", "providers": available_providers()}


@app.post("/api/chat")
async def chat(req: ChatRequest) -> JSONResponse:
    msgs = [m.model_dump() for m in req.messages if m.content.strip()]
    if not msgs:
        return JSONResponse({"error": "Tom fråga"}, status_code=400)
    try:
        result = await generate(msgs)
        return JSONResponse(result)
    except ProviderError as e:
        return JSONResponse({"error": str(e)}, status_code=502)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")
