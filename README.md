# Testbot (arbetsnamn)

En **lokal AI-assistent som bara kan IT-test och kvalitetssäkring**.
Körs på din dator, öppnas i webbläsaren (app-känsla), svarar helst på svenska,
**visar alltid källor**, och går att **kvalitetssäkra** (verifiera/markera fel).

> Status: **Fas 1 + 2 klara** — MVP-chatt i webbläsaren (svenska, "bara test", provider-pool) **plus
> kunskapsbas (RAG) med lokala embeddings och källor i svaren**. Webbsök + kvalitetssäkring kommer i fas 3–4 (se `docs/roadmap.md`).

## Mål (från Simons krav)
- Användningsområden: **allt** — tutor (förklara/quiz), slå upp & sammanfatta källor, hjälpa skriva tester/teststrategier.
- **Privat**, men ska gå att **dela med en vän** om möjligt.
- Kan använda **kursmaterial om man lägger in det** — men är **fristående** (bygger på internet-info, inte beroende av kursen).
- **Svenska** i första hand.
- Källor: **både** kurerad samling **och** webbsök mot vitlista.
- **Alltid källor/citat.**
- Kunna **markera svar som verifierade/felaktiga**. Granskningsläge finns som **valfritt** QA-stöd.
- **Helt gratis** (öppen källkod / gratistjänster).
- Privat sidoprojekt.

## Snabbstart
```bash
cd ~/ws/testbot
./start.sh          # startar servern (om den inte kör) och öppnar webbläsaren
# eller: .venv/bin/uvicorn app.main:app --port 8765
# öppna http://127.0.0.1:8765
```
Nycklar ligger i `.env` (committas aldrig). Provider-pool: Groq → Gemini → Ollama (lokal fallback).

## Struktur
```
testbot/
├── README.md
├── docs/
│   ├── arkitektur.md     ← komponenter, dataflöde, design
│   └── roadmap.md        ← faser + status
├── app/                  ← backend (FastAPI) — byggs i fas 1+
├── web/                  ← frontend (HTML/JS) — byggs i fas 1
└── data/                 ← kunskapsbas, embeddings, loggar (gitignoreras)
```
