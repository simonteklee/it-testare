Hej! Här är IT-testare — en liten gratis AI-assistent som bara kan IT-test & kvalitetssäkring.
Den körs på din egen dator (inget konto behövs, allt är lokalt).

Så här gör du (Windows):
1) Öppna PowerShell: tryck på Windows-tangenten, skriv "PowerShell" och tryck Enter.
2) Klistra in raden nedan och tryck Enter:

irm https://raw.githubusercontent.com/simonteklee/it-testare/main/install.ps1 | iex

   (Får du ett fel om "execution policy" – kör först denna rad, sen raden ovan:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)

3) Skriptet öppnar två webbsidor och ber om två gratisnycklar (Groq + Gemini).
   Logga in, klicka "Create API key", kopiera och klistra in i PowerShell-fönstret. Tryck Enter.
4) Klart! Boten öppnas i webbläsaren på http://127.0.0.1:8765

Nästa gång du vill starta: gå in i mappen "it-testare" (i din hemkatalog) och dubbelklicka på start.cmd.

Vill du dela kunskap med mig? Klistra in detta id under "delad bas" i knappen 💡 tips & dela,
klicka Spara och sedan Synka:
82014cbacdd3ad803af69597106c5538
