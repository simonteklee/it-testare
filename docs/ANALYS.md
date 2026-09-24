# Varför TestARN är krångligt att sätta upp — och hur vi förenklar det

_Genomgång 2026-09-24. Bakgrund: klasskompisar fick "127.0.0.1 refused to connect"
och vi ville förstå varför det blir krångligt och buggigt._

## Kort sammanfattning

Krånglet kommer inte från själva appen, utan från **tre saker runt omkring**:
1. **Tunga/ovissa beroenden** (uv + egen Python, `fastembed`).
2. **Många nätverkssteg** vid installation (GitHub, PyPI, uv, modell).
3. **Tysta fel** — när något gick fel syntes inget, bara en tom sida.

Dessutom saknades en enkel **"radera och börja om"**.

---

## Varför det är komplicerat

| Orsak | Vad som händer | Åtgärd |
|---|---|---|
| **uv + egen Python** | uv bygger `.exe`-stubbar ("trampolines"). På vissa Windows kan de inte starta Python-barnet → appen startar inte alls. | Installeraren **föredrar nu systemets Python** (`python -m venv` + pip). uv används bara som reserv om Python saknas. Alla startskript kör `python -m uvicorn` (går runt stubben). |
| **`fastembed`** | Drar in onnxruntime/tokenizers (~100–200 MB) och används bara för **embeddings** i kunskapsbasen. Största enskilda installationsrisken. | **Förslag:** gör embeddings valfritt — appen körs med enkel nyckelordssökning i kunskapsbasen om modellen inte finns. |
| **Två API-nycklar** | Man måste skaffa **både** Groq och Gemini innan första starten. | **Förslag:** en nyckel räcker (provider-poolen växlar redan), och appen ska kunna starta utan nyckel (då bara utan svar). |
| **Många nätsteg** | GitHub-API → PyPI → uv → ev. modellnedladdning. Varje steg kan blockas av nätverk/antivirus. | System-Python-vägen tar bort uv-steget. Logg + tydliga fel (se nedan). |
| **Ingen avinstallation** | Gick något sönder fanns inget rent sätt att börja om. | **Klart:** dold **"🗑 Avinstallera"** i *💡 tips & dela* (tre steg) som stoppar appen och raderar mapp + genvägar. |

## Varför buggar kommer

| Orsak | Exempel | Åtgärd |
|---|---|---|
| **Tredjepartstjänster** | Delningen gick via en GitHub-gist — bara **ägaren** kunde skriva → ingen såg andras frågor. | Bytte till **ntfy.sh** (inga konton). |
| **Tysta fel** | En massa `except Exception: pass` — fel försvann utan spår. | Påbörjat: startskript visar nu felet och loggar (`testarn.log` / `/tmp/testarn.log`). Bör rensas vidare. |
| **Bräcklig parsning** | `search.py` skrapar DuckDuckGo:s HTML med regex — går sönder när de ändrar sin sida. | **Förslag:** felmeddelande i UI när sökningen ger 0 träffar (i stället för tyst tomt). |
| **Miljöberoenden** | PDF/Office kräver `pdftotext`/LibreOffice på vissa format. | Finns redan fallbacks (pypdf, python-docx/pptx/openpyxl). |

---

## Vad som gjorts (v1.7.3 → 1.8.0)

- **Synliga fel:** `start.sh` skriver ut felet om servern inte startar; Windows loggar till
  `testarn.log` och visar loggvägen. Nytt `start-debug.sh` / `start-debug.cmd`.
- **Går runt uv-stubben:** `python -m uvicorn` överallt.
- **Robust installer:** föredrar systemets Python, faller tillbaka på uv, självtestar miljön.
- **Avinstallera:** dold knapp (tre steg) → stoppar appen + raderar mapp och genvägar.
- **Klassens frågor** delas via ntfy (inga nycklar).

## Förslag att ta nästa vecka

1. Gör `fastembed` **valfritt** (nyckelordssökning som fallback) → mycket lättare install.
2. Låt **en** API-nyckel räcka; tillåt start utan nyckel.
3. Rensa tysta `except: pass` → logga i stället.
4. Överväg en **färdig .exe** (inbäddad Python) så att kompisarna slipper installera Python/uv alls.
