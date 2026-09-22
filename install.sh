#!/usr/bin/env bash
# IT-testare — engångsinstallation. Enklaste vägen:
#   curl -fsSL <LÄNK> | bash
# eller: bash install.sh
set -euo pipefail

PKG_URL="${IT_TESTARE_PKG_URL:-}"
DIR="${IT_TESTARE_DIR:-$HOME/it-testare}"

echo "== IT-testare installeras till $DIR =="

if ! command -v python3 >/dev/null 2>&1; then
  echo "✗ Python 3 saknas. Installera det först:"
  echo "   Debian/Ubuntu/Mint:  sudo apt install python3 python3-venv"
  echo "   Fedora:              sudo dnf install python3"
  echo "   macOS:               brew install python"
  echo "  … och kör sedan detta igen."
  exit 1
fi

if [ -z "$PKG_URL" ]; then
  echo "✗ Ingen paketlänk (IT_TESTARE_PKG_URL) angiven."
  exit 1
fi

mkdir -p "$DIR"; cd "$DIR"

echo "• hämtar programmet…"
curl -fsSL "$PKG_URL" -o pkg.b64
if base64 -d pkg.b64 > pkg.zip 2>/dev/null; then :; else base64 -D pkg.b64 > pkg.zip; fi
if command -v unzip >/dev/null 2>&1; then unzip -oq pkg.zip; else
  python3 -c "import zipfile; zipfile.ZipFile('pkg.zip').extractall('.')"
fi
rm -f pkg.b64 pkg.zip

echo "• skapar python-miljö och installerar (tar ~1 min)…"
# Använd uv (fristående, kräver inte python3-venv)
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  echo "  installerar uv…"
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || true
fi
UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
if [ -x "$UV" ] || command -v "$UV" >/dev/null 2>&1; then
  "$UV" venv .venv --python 3.12 >/dev/null 2>&1 || "$UV" venv .venv
  "$UV" pip install -q -r requirements.txt
else
  # fallback: vanlig venv (kan kräva python3-venv-paketet)
  python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip >/dev/null 2>&1 || true
  .venv/bin/pip install -q -r requirements.txt
fi

# Nycklar
if [ -n "${GROQ_API_KEY:-}" ] && [ -n "${GEMINI_API_KEY:-}" ]; then
  GROQ="$GROQ_API_KEY"; GEM="$GEMINI_API_KEY"
else
  echo
  echo "== Två gratis nycklar behövs (2 min) =="
  echo "  1) Groq:   https://console.groq.com/keys   → Create API Key"
  echo "  2) Gemini: https://aistudio.google.com/apikey → Create API key"
  read -rp "Klistra in GROQ-nyckel (gsk_...): " GROQ < /dev/tty
  read -rp "Klistra in GEMINI-nyckel: " GEM < /dev/tty
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
echo "✓ Klart! Startar IT-testare…"
./start.sh
echo "Öppna webbläsaren på: http://127.0.0.1:8765"
echo "Nästa gång: kör  $DIR/start.sh"
