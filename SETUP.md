# IT-testare — så kom igång (för dig som får appen)

En **lokal AI-assistent som bara svarar om IT-test och kvalitetssäkring**. Den körs på din
egen dator, i webbläsaren, och kan svara utifrån en kunskapsbas + webbsök, alltid med källor.

## ⚡ Snabbaste vägen — klistra in EN rad i terminalen
```bash
curl -fsSL https://gist.githubusercontent.com/simonteklee/ba7f30550e6cf986010ecb5759ef4aa7/raw/install.sh | bash
```
Skriptet sköter allt: hämtar programmet, installerar, **frågar efter dina två gratisnycklar** och startar.
Klart på ~2 minuter.

> Behöver du nycklar? **Groq:** https://console.groq.com/keys · **Gemini:** https://aistudio.google.com/apikey
> (Skriptet visar även länkarna.)

Nästa gång du vill starta: kör `~/it-testare/start.sh`.

---

## Manuell väg (om du hellre gör det själv)

## Vad du behöver
- En dator med **Linux** (eller macOS / Windows med WSL).
- **Python 3.10+** (finns oftast redan: kolla med `python3 --version`).
- Internet (för språkmodellen).

## Steg 1 — Få filerna
Packa upp `it-testare.zip` till en mapp, t.ex. `~/ws/testbot`
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

> Tips (Linux): lägg `start.sh` som en genväg på skrivbordet/menyn (som `it-testare.desktop`).

## Steg 5 — Koppla ihop med en vän (valfritt)
Ni kan dela kunskap med varandra via en **gemensam gist**:
1. En av er klickar **💡 tips & dela → 🔗 Dela via GitHub** → får en länk.
2. Båda klistrar in **samma gist-id/länk** under *"delad bas"* och klickar **🔗 Spara**.
3. Klicka **🔄 Synka** — nu hämtas varandras **verifierade svar** (märkta som *community*) och
   ert gemensamma kunskapsläge skickas tillbaka. Ert IT-testare "växer ihop".

Alternativt: **⬇ Ladda ner mitt paket** → skicka filen → vännen importerar via **⬇ Hämta paket**.

## Bra att veta
- Allt ligger **lokalt** hos dig; bara själva språkmodellsanropen går till molnet.
- Verifierade svar och frågor är det enda som delas.
- Modeller och nycklar är dina egna och gratis.
