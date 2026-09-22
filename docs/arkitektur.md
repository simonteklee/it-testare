# Arkitektur — Testbot

> Ett lokalt, gratis, AI-assistent som **bara** rör IT-test och kvalitetssäkring.
> Designen är gjord för Simons dator (Ryzen 5 4500U, 7 GB RAM, integrerat grafikkort)
> och för att kunna byggas steg för steg och förstås.

## Principer
1. **Bara test** — modellen ska hålla sig till IT-test/QA. Utanför ämnet → artigt avvisande.
2. **Alltid källor** — varje svar får klickbara referenser (webb + kunskapsbas).
3. **Kvalitetssäkring** — du kan markera svar som *verifierade* eller *felaktiga*; sparas och används.
4. **Gratis** — gratistjänster/open source, ingen kostnad.
5. **Fristående** — internetbaserad grund; ditt kursmaterial är ett *valfritt* tillägg.
6. **Provider-agnostiskt** — LLM:en ska gå att byta utan att röra resten.
7. **Lokal kärna** — app + data på din dator; endast själva språkmodellen kan ligga i molnet.

## Komponenter
| Komponent | Roll | Teknik (förslag) |
|-----------|------|------------------|
| Frontend | Chatt-UI i webbläsaren, app-känsla | Enkel HTML/CSS/JS + `.desktop`-genväg |
| Backend | API, orkestrering, "bara test"-lager | Python + FastAPI (körs lokalt på localhost) |
| LLM-lager | Svar på svenska | Provider-agnostiskt; **Google Gemini (gratis)** standard, kan bytas |
| Ämneskontroll | Hålla sig till test | Systemprompt + domänklassning (avvisa off-topic) |
| Kunskapsbas (RAG) | Kuraterade testdokument | Lokala **gratis embeddings** + vektordatabas (Chroma/LanceDB) |
| Webbsök | Aktuell info från nätet | Gratis (DuckDuckGo/SearXNG) mot **vitlista** av testkällor |
| Citat | Källor i svaret | Länkar + källutdrag (snippet) |
| Kvalitetssäkring | Verifiera/fela | Feedback-API + "verifierade svar"-lager + valfritt granskningsläge |

## Dataflöde
```
Fråga
  └─► Ämneskontroll (IT-test?)
        ├─ nej → artigt avvisande + förslag på vad boten kan
        └─ ja
            ├─► Sök i kunskapsbas (RAG)  ─┐
            └─► Webbsök (vitlista)       ─┤
                                          ▼
                           Sammanställ kontext + källor
                                          ▼
                    LLM (svenska, "bara test", svara med citat)
                                          ▼
                         Svar  +  klickbara källor
                                          ▼
                         Feedback: 👍/👎  ·  "Verifiera"
```

## "Bara test"-lagret (det unika)
- **Prompt**: tydlig roll ("du är expert på IT-test och kvalitetssäkring, avvisa annat").
- **Domänfilter**: klassificera frågan; om off-topic → avvisa (kan vara en billig LLM-koll).
- **Källor**: webbsök begränsas till kurerade test-domäner (vitlista i `data/källor.yaml`).
- **Kunskapsbas**: seedas med erkända källor (ISTQB-syllabus, Ministry of Testing, Guru99,
  böcker som *Agile Testing* / *Lessons Learned in Software Testing* m.fl.).

## Kvalitetssäkring
- Varje svar får en **källa**. Du kan:
  - 👍 *stämmer* / 👎 *fel*,
  - markera **"Verifierad av mig"** → svaret blir en del av en betrodd kunskapsbank.
- **Granskningsläge** (valfritt, avstängt som standard): nya kunskapsbas-inlägg väntar på ditt godkännande.
- Allt loggas lokalt (`data/`).

## Beslut & öppna frågor
- **LLM-provider:** Google Gemini gratis (standard) — *bekräfta*. Alternativ: Groq, OpenRouter (gratis modeller), lokal Ollama.
- **Namn på boten:** ej bestämt.
- **Delning till vän:** senare fas — antingen "kör själv"-paket (kräver egen nyckel) eller liten gratis host.

## Icke-mål (just nu)
- Inte produktionssäker multi-användartjänst.
- Inte 100 % filtrering av *hela* internet — vi använder kurerade källor + vitlista + prompt.
