# Roadmap — Testbot

Byggs fas för fas. Efter varje fas kör vi och kollar att det funkar innan nästa.

## Fas 0 — Beslut ✅ (pågår)
- [x] Krav insamlade (se `README.md`).
- [x] Arkitektur skissad (`docs/arkitektur.md`).
- [ ] Välj **gratis LLM-nyckel** (förslag: Google Gemini).  ← **väntar på Simon**
- [ ] Bestäm **namn** på boten.

## Fas 1 — MVP: chatt i webbläsaren
- [ ] FastAPI-backend som körs lokalt.
- [ ] Enkel chatt-frontend (HTML/JS) i webbläsaren.
- [ ] LLM-koppling (Gemini gratis) med **svenska**.
- [ ] "Bara test"-systemprompt + avvisande av off-topic.
- [ ] Källor/citat för webbresultat (första versionen).
- [ ] `.desktop`-genväg → känns som en app.

## Fas 2 — Kunskapsbas (RAG)
- [ ] Lokala embeddings (gratis) + vektordatabas.
- [ ] Inläsning av dokument (PDF/md) → kunskapsbas.
- [ ] Kuraterade testkällor som grund (ISTQB m.fl.).
- [ ] Valfritt: lägg in kursmaterial.

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
