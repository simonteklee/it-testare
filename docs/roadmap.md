# Roadmap — Testbot

Byggs fas för fas. Efter varje fas kör vi och kollar att det funkar innan nästa.

## Fas 0 — Beslut ✅ (pågår)
- [x] Krav insamlade (se `README.md`).
- [x] Arkitektur skissad (`docs/arkitektur.md`).
- [ ] Välj **gratis LLM-nyckel** (förslag: Google Gemini).  ← **väntar på Simon**
- [ ] Bestäm **namn** på boten.

## Fas 1 — MVP: chatt i webbläsaren ✅
- [x] FastAPI-backend som körs lokalt (`app/main.py`).
- [x] Enkel chatt-frontend (HTML/JS) i webbläsaren (`web/index.html`).
- [x] LLM-koppling med **svenska** + provider-pool (Groq → Gemini → Ollama) (`app/llm.py`).
- [x] "Bara test"-systemprompt + avvisande av off-topic (`app/prompt.py`).
- [x] `.desktop`-genväg → känns som en app (`start.sh`, `it-testare.desktop`).
- [ ] Källor/citat för webbresultat — flyttat till fas 3.

## Fas 2 — Kunskapsbas (RAG) ✅
- [x] Lokala embeddings (gratis, ingen kvot) — `fastembed` + `paraphrase-multilingual-MiniLM-L12-v2`.
- [x] Inläsning av dokument/URL:er via `ingest.py` (html + PDF).
- [x] Kuraterade testkällor inlästa (sv/en Wikipedia: programvarutestning, software testing, regression, QA). **155 stycken.**
- [x] Källor visas i svaren (nummer [1]..[n] + käll-lista).
- [ ] Valfritt: lägg in kursmaterial (`ingest.py <fil>`).

## Fas 3 — Webbsök mot vitlista
- [ ] Gratis webbsök (DuckDuckGo/SearXNG).
- [ ] Vitlista av test-domäner (`data/källor.yaml`).
- [ ] Svar som väver samman kunskapsbas + webb, alltid med källor.

## Fas 4 — Kvalitetssäkring
- [ ] 👍/👎-feedback som sparas.
- [ ] "Verifierad"-markering → betrodd kunskapsbank.
- [ ] Valfritt granskningsläge.

## Fas 5 — Paketera & dela
- [ ] App-genväg/skript för enkel start.
- [ ] Alternativ för att dela med en vän.
