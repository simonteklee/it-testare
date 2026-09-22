"""Provider-lager: moln-pool (Groq, Gemini) + lokal fallback (Ollama).

Försöker i ordning och faller vidare om en provider är otillgänglig/takad.
"""
from __future__ import annotations

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from .prompt import SYSTEM_PROMPT

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")

TIMEOUT = httpx.Timeout(120.0, connect=10.0)


class ProviderError(Exception):
    pass


async def _groq(messages: list[dict]) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        "max_tokens": 1024,
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.post(url, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=payload)
        if r.status_code != 200:
            raise ProviderError(f"groq {r.status_code}: {r.text[:200]}")
        return r.json()["choices"][0]["message"]["content"]


async def _gemini(messages: list[dict]) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    contents = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.3},
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.post(url, headers={"x-goog-api-key": GEMINI_API_KEY}, json=payload)
        if r.status_code != 200:
            raise ProviderError(f"gemini {r.status_code}: {r.text[:200]}")
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


async def _ollama(messages: list[dict]) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        "stream": False,
        "options": {"num_ctx": 4096},
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=5.0)) as c:
        r = await c.post(f"{OLLAMA_URL}/api/chat", json=payload)
        if r.status_code != 200:
            raise ProviderError(f"ollama {r.status_code}")
        return r.json()["message"]["content"]


# Poolordning: moln först (snabbt + bäst kvalitet), lokal som sista fallback.
PROVIDERS = [
    ("groq", lambda: GROQ_API_KEY, _groq, GROQ_MODEL),
    ("gemini", lambda: GEMINI_API_KEY, _gemini, GEMINI_MODEL),
    ("ollama", lambda: True, _ollama, OLLAMA_MODEL),
]


def available_providers() -> list[dict]:
    return [
        {"name": n, "model": m, "ready": bool(k())}
        for n, k, _, m in PROVIDERS
    ]


async def generate(messages: list[dict]) -> dict:
    """Returnerar {answer, provider, model}. Faller vidare vid fel/tak."""
    errors = []
    for name, key_fn, fn, model in PROVIDERS:
        if not key_fn():
            continue
        try:
            answer = await fn(messages)
            if answer and answer.strip():
                return {"answer": answer.strip(), "provider": name, "model": model}
            errors.append(f"{name}: tomt svar")
        except ProviderError as e:
            errors.append(str(e))
        except Exception as e:  # nätverk/timeout
            errors.append(f"{name}: {type(e).__name__}: {e}")
    raise ProviderError("Ingen provider kunde svara. " + " | ".join(errors))
