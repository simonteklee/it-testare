# Bidra

Tack för att du vill hjälpa till! 🙌

## Kom igång
1. Forka repot och klona det.
2. `uv venv .venv && uv pip install -r requirements.txt`
3. `cp .env.example .env` och fyll i egna gratisnycklar (Groq + Gemini).
4. Kör: `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765`.

## Riktlinjer
- Håll koden enkel och läsbar; små moduler med tydligt ansvar (se `docs/ARKITEKTUR.md`).
- Håll dig till **svenska** i gränssnitt och svar.
- Committa **aldrig** nycklar, `.env` eller `data/`.
- Beskriv i PR:en *vad* och *varför*.

## Idéer / att göra
Se `docs/roadmap.md`.
