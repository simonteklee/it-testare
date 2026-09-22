# Arkitektur

IT-testare är en **lokal webbapp**: en liten FastAPI-server på `127.0.0.1:8765` som serverar ett
enkelt gränssnitt och orkestrerar språkmodeller, kunskap och delning.

```
web/index.html  ──HTTP──►  app/main.py (FastAPI)
                               │
        ┌──────────────────────┼───────────────────────────┐
        ▼                      ▼                           ▼
   app/llm.py            app/kb.py + app/extract.py    app/community.py + app/share.py
 (Groq/Gemini/Ollama)   (embeddings + dokument)        (delad gist: frågor & svar)
        │                      │
        └────────► app/search.py (webbsök, vitlista)
                               │
                        app/feedback.py (👍/👎/verifiera)
```

## Moduler

| Fil | Ansvar |
|-----|--------|
| `app/main.py` | FastAPI-appen, endpoints, orkestrering |
| `app/prompt.py` | "Bara test"-systemprompten |
| `app/llm.py` | Provider-pool: Groq → Gemini → Ollama, med fallback |
| `app/kb.py` | Kunskapsbas: lokala embeddings (`fastembed`) + JSONL-vektorlager, dedupe |
| `app/extract.py` | Textextrahering (pdf/docx/pptx/xlsx/html/txt) + chunkning + webbsida |
| `app/search.py` | Webbsök (DuckDuckGo) filtrerat mot vitlista/nyckelord |
| `app/feedback.py` | 👍/👎, verifiering, granskningsläge, config |
| `app/share.py` | Delningspaket + GitHub Gist (token via `gh` eller `GH_TOKEN`) |
| `app/community.py` | Gemensam Q&A-bas (frågor & svar delas via gist) |
| `ingest.py` | CLI för att läsa in filer/URL:er i kunskapsbasen |

## Dataflöde (en fråga)

1. Frågan loggas lokalt (`data/qa.jsonl`) och går genom "bara test"-lagret (prompt).
2. Relevant kontext hämtas från kunskapsbasen (`kb.search`) och ev. webbsök (`search.search`).
3. Kontexten läggs in i systemprompten och skickas till provider-poolen.
4. Svaret returneras med källor (`kb` / `web` / `community`) och sparas.
5. Användaren kan 👍/👎 eller **verifiera** (→ betrodd kunskapsbank).
6. Vid **Synka** slås lokala frågor & svar ihop med gruppens (dedupe) och skickas till den delade gisten.

## Designprinciper

- **Lokalt först.** Appen, datan och embeddings körs lokalt. Endast LLM-anropet går till molnet.
- **Gratis.** Gratisnivåer + lokal embeddings; inga kort.
- **Provider-agnostiskt.** LLM-lagret kan bytas utan att röra resten.
- **Fel-tolerant.** Poolen faller vidare vid tak/fel; installationen kraschar inte på en detalj.
- **Transparens.** Alltid källor; verifierade svar märks.

## Datamodell (lokala filer, `data/` – gitignoreras)

- `kb.jsonl` – kunskapsbasen (text, källa, url, kind, vektor, hash)
- `qa.jsonl` – lokala frågor & svar
- `community_qa.jsonl` – hämtade (gruppens) frågor & svar
- `feedback.jsonl` / `pending.jsonl` – kvalitetssäkring
- `config.json` – inställningar (granskningsläge, gemensam bas, delad gist)
- `uploads/` – uppladdade filer

## Vidareutveckling

Se [`roadmap.md`](roadmap.md).
