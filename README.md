# Testbot (arbetsnamn)

En **lokal AI-assistent som bara kan IT-test och kvalitetssäkring**.
Körs på din dator, öppnas i webbläsaren (app-känsla), svarar helst på svenska,
**visar alltid källor**, och går att **kvalitetssäkra** (verifiera/markera fel).

> Status: **planeringsfas.** Arkitektur och roadmap finns i `docs/arkitektur.md`.
> Ingen fungerande kod än — vi bygger fas för fas (se roadmap) och Simon kan följa varje steg.

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

## Snabbstart (kommer)
```bash
# när fas 1 är klar
cd ~/ws/testbot
cp .env.example .env      # klistra in din gratis API-nyckel
uv run uvicorn app.main:app --reload
# öppna http://localhost:8000
```

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
