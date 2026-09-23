#!/usr/bin/env bash
# TestARN - engangsinstallation.
#   curl -fsSL https://raw.githubusercontent.com/simonteklee/it-testare/main/install.sh | bash
set -euo pipefail

PKG_URL="${IT_TESTARE_PKG_URL:-https://codeload.github.com/simonteklee/it-testare/tar.gz/refs/heads/main}"
DIR="${IT_TESTARE_DIR:-$HOME/it-testare}"

echo "== TestARN installeras till $DIR =="

if ! command -v python3 >/dev/null 2>&1 && ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  echo "! Varken python3 eller uv hittades. Installera python3 (t.ex. sudo apt install python3) och kor igen."
  exit 1
fi

mkdir -p "$DIR"
echo "• hamtar programmet..."
curl -fsSL "$PKG_URL" -o /tmp/it-testare-pkg.tar.gz
tar -xzf /tmp/it-testare-pkg.tar.gz -C "$DIR" --strip-components=1
rm -f /tmp/it-testare-pkg.tar.gz
cd "$DIR"

echo "• skapar python-miljo och installerar (tar ~1 min)..."
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  echo "  installerar uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || true
fi
UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
if [ -x "$UV" ] || command -v "$UV" >/dev/null 2>&1; then
  rm -rf .venv
  "$UV" venv .venv --python 3.12 >/dev/null 2>&1 || "$UV" venv .venv
  "$UV" pip install -q -r requirements.txt
else
  rm -rf .venv
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

# Nycklar
if [ -n "${GROQ_API_KEY:-}" ] && [ -n "${GEMINI_API_KEY:-}" ]; then
  GROQ="$GROQ_API_KEY"; GEM="$GEMINI_API_KEY"
else
  echo
  echo "== Tva gratis nycklar behovs (2 min) =="
  echo "Skapa en nyckel, kopiera den och klistra in har."
  echo "--- Nyckel 1 av 2: GROQ ---"
  (xdg-open "https://console.groq.com/keys" >/dev/null 2>&1 || open "https://console.groq.com/keys" >/dev/null 2>&1 || true) &
  read -rp "  Klistra in GROQ-nyckeln (gsk_...) och tryck Enter: " GROQ < /dev/tty
  echo "--- Nyckel 2 av 2: GEMINI ---"
  (xdg-open "https://aistudio.google.com/apikey" >/dev/null 2>&1 || open "https://aistudio.google.com/apikey" >/dev/null 2>&1 || true) &
  read -rp "  Klistra in GEMINI-nyckeln och tryck Enter: " GEM < /dev/tty
fi

cat > .env <<EOF
GROQ_API_KEY=$GROQ
GEMINI_API_KEY=$GEM
GROQ_MODEL=openai/gpt-oss-120b
GEMINI_MODEL=gemini-3.6-flash
EMBED_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EOF
chmod 600 .env
chmod +x start.sh

echo
echo "✓ Klart! Startar TestARN..."
./start.sh
echo "Oppna webblasaren pa: http://127.0.0.1:8765"
echo "Nasta gang: kor $DIR/start.sh"
