Hej! Här är TestARN — en liten gratis AI-assistent som bara kan IT-test & kvalitetssäkring.
Den körs på din egen dator (inget konto behövs, allt är lokalt).

Så här gör du:
1) Öppna en Terminal. På Linux: tryck Ctrl+Alt+T.
2) Klistra in den här raden och tryck Enter (klistra in med Ctrl+Shift+V):

curl -fsSL "https://raw.githubusercontent.com/simonteklee/testarn/main/install.sh?v=$(date +%s)" | bash

3) Skriptet öppnar två webbsidor och ber om två gratisnycklar (Groq + Gemini).
   Logga in, klicka "Create API key", kopiera och klistra in i terminalen. Tryck Enter.
   (Det syns inget när du klistrar in — det är normalt.)
4) Klart! Boten öppnas i webbläsaren på http://127.0.0.1:8765

Frågor delas automatiskt med klassen – inget att klistra in.
Starta appen så syns allas frågor under 📁 Klassens frågor.
