# Dela & klassens frågor

TestARN körs lokalt hos var och en. Kopplingen mellan användare sker via **ntfy.sh**
(en gratis meddelandetjänst utan konto) – ingen nyckel och inget id att klistra in.

## Klassens frågor (på som standard)

Varje fråga du ställer delas **automatiskt** till klassens gemensamma rum. Allas frågor
visas under **📁 Klassens frågor** – med datum och vem som ställde dem. Klicka på en fråga
för att återanvända den som din egen prompt.

- Inget att koppla: standardrummet är förvalt i appen.
- Fungerar för alla direkt efter installation – **inga nycklar, ingen inloggning**.
- Stäng av/för på med kryssrutan **🌍 Klassens frågor** i panelen *💡 tips & dela*.

Så här funkar det tekniskt: varje fråga publiceras som ett litet meddelande till en gemensam
ntfy-*topic*, och varje app hämtar de senaste meddelandena och slår ihop dem med sina egna
(dubbletter av samma frågetext tas bort). Appen kommer ihåg allt lokalt i
`data/community_qa.jsonl`, så listan finns kvar även när ntfy:s cache (ca 12 h) rensat gamla meddelanden.

## Vad delas?

- **Fråga + svar** (text) – så att klassen kan lära av varandra.
- Inte dina filer, nycklar, inställningar eller annat lokalt.

Stäng av **🌍 Klassens frågor** om du vill att dina frågor stannar lokalt.

## Eget rum (frivilligt)

Vill ni ha ett eget rum istället för standardrummet: sätt en egen topic i `data/config.json`
(`"qa_topic": "ert-namn"`) på alla installationer. (Standardrummet är
`testarn-fragor-7b3d91c4`.)

## Verifierade svar via länk (valfritt)

Vill ni dela **verifierade svar** (👍/✅) med en vän i stället:

1. Klicka **💡 tips & dela → 🔗 Dela via GitHub** → du får en länk.
2. Vännen klistrar in länken under *"delad bas"* → **🔗 Spara** → **🔄 Synka**.

Alternativt: **⬇ Ladda ner mitt paket** → skicka filen → vännen importerar via **⬇ Hämta paket**.

## Dela appen med fler

Skicka installationsraden – se [`SETUP.md`](../SETUP.md) och färdiga texter i
`SKICKA-TILL-VAN.md` / `SKICKA-TILL-VAN-WINDOWS.md`.

## Integritet

Rummet för klassens frågor är **öppet för den som känner till topic-namnet** och ska inte
betraktas som privat. Dela inget känsligt i frågorna om rummet har många medlemmar.
