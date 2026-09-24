# TestARN — så kom igång (för dig som får appen)

En **lokal AI-assistent som bara svarar om IT-test och kvalitetssäkring**. Den körs på din
egen dator, i webbläsaren, och kan svara utifrån en kunskapsbas + webbsök, alltid med källor.

## ⚡ Snabbaste vägen — klistra in EN rad i terminalen
```bash
curl -fsSL "https://raw.githubusercontent.com/simonteklee/testarn/main/install.sh?v=$(date +%s)" | bash
```
Skriptet sköter allt: hämtar programmet, installerar, **frågar efter dina två gratisnycklar** och startar.
Klart på ~2 minuter.

> Behöver du nycklar? **Groq:** https://console.groq.com/keys · **Gemini:** https://aistudio.google.com/apikey
> (Skriptet visar även länkarna.)

Nästa gång du vill starta: kör `~/testarn/start.sh`.

---

## Manuell väg (om du hellre gör det själv)

## Vad du behöver
- En dator med **Linux** (eller macOS / Windows med WSL).
- **Python 3.10+** (finns oftast redan: kolla med `python3 --version`).
- Internet (för språkmodellen).

## Steg 1 — Få filerna
Packa upp `testarn.zip` till en mapp, t.ex. `~/ws/testbot`
(eller `git clone` om du fått ett repo).

## Steg 2 — Installera
```bash
cd ~/ws/testbot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
> Har du `uv` (rekommenderas): `uv venv .venv && uv pip install -r requirements.txt`

## Steg 3 — Skaffa gratis API-nycklar
- **Groq** (snabb): https://console.groq.com/keys → *Create API Key*
- **Google Gemini**: https://aistudio.google.com/apikey → *Create API key*

Skapa `.env` (kopiera `.env.example`) och klistra in nycklarna:
```
GROQ_API_KEY=...
GEMINI_API_KEY=...
```

## Steg 4 — Starta
```bash
./start.sh
```
Öppnas inte webbläsaren automatiskt → gå till **http://127.0.0.1:8765**

> Tips (Linux): lägg `start.sh` som en genväg på skrivbordet/menyn (som `testarn.desktop`).

## Steg 5 — Klassen delar frågor automatiskt
Inget att koppla eller klistra in: **Klassens frågor** är på som standard. Varje fråga du ställer
delas till klassens gemensamma rum (via ntfy.sh – gratis, inga nycklar) och allas frågor syns under
**📁 Klassens frågor** med vem som frågat. Stäng av med kryssrutan **🌍 Klassens frågor** i *💡 tips & dela*.

Vill ni hellre dela **verifierade svar** via en länk: **💡 tips & dela → 🔗 Dela via GitHub** (eller
**⬇ Ladda ner mitt paket** och skicka filen → vännen importerar via **⬇ Hämta paket**).

## Bra att veta
- Allt ligger **lokalt** hos dig; bara själva språkmodellsanropen går till molnet.
- **Klassens frågor** (fråga + svar) delas automatiskt; verifierade svar delas bara om du aktivt synkar.
- Modeller och nycklar är dina egna och gratis.

---

## Windows
Öppna **PowerShell** (Windows-tangenten → skriv "PowerShell" → Enter) och kör:
```powershell
irm "https://raw.githubusercontent.com/simonteklee/testarn/main/install.ps1?v=$((Get-Random))" | iex
```
Blockerar Windows skriptet? Kör först:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Skriptet installerar allt (via `uv`, inget Python-krav), frågar efter nycklarna och startar.
Starta om senare: dubbelklicka **`start.cmd`** i mappen `testarn`.

> Obs: filuppladdning av **PDF/Word/PowerPoint/Excel** fungerar även på Windows (inbyggd läsning via Python).
> Vissa format (odt/rtf) kan kräva LibreOffice – annars konvertera till PDF/docx.
