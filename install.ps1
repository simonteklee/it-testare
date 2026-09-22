# IT-testare - Windows-installation (PowerShell).
# Enklaste vägen (i PowerShell):
#   irm https://gist.githubusercontent.com/simonteklee/ba7f30550e6cf986010ecb5759ef4aa7/raw/install.ps1 | iex
$ErrorActionPreference = "Stop"

$dir = if ($env:IT_TESTARE_DIR) { $env:IT_TESTARE_DIR } else { "$HOME\it-testare" }
$pkgUrl = "https://gist.githubusercontent.com/simonteklee/ba7f30550e6cf986010ecb5759ef4aa7/raw/it-testare.b64"

Write-Host "== IT-testare installeras till $dir ==" -ForegroundColor Cyan

# 1) uv (fixar Python automatiskt, inget Python-krav)
if (-not (Get-Command uv -ErrorAction SilentlyContinue) -and -not (Test-Path "$HOME\.local\bin\uv.exe")) {
    Write-Host "• installerar uv (pakethanterare)..."
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
}
$env:Path = "$HOME\.local\bin;$env:Path"
$uv = if (Get-Command uv -ErrorAction SilentlyContinue) { "uv" } else { "$HOME\.local\bin\uv.exe" }

# 2) hämta programmet
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Set-Location $dir
Write-Host "• hämtar programmet..."
Invoke-WebRequest -Uri $pkgUrl -OutFile "pkg.b64"
$b64 = (Get-Content "pkg.b64" -Raw) -replace "\s", ""
[IO.File]::WriteAllBytes("$dir\pkg.zip", [Convert]::FromBase64String($b64))
Expand-Archive -Path "pkg.zip" -DestinationPath $dir -Force
Remove-Item pkg.b64, pkg.zip -Force

# 3) miljö + paket
Write-Host "• installerar (tar ~1 min)..."
if (Test-Path ".venv") { Remove-Item ".venv" -Recurse -Force }
& $uv venv .venv
& $uv pip install -q -r requirements.txt

# 4) nycklar
$groq = $env:GROQ_API_KEY; $gem = $env:GEMINI_API_KEY
if (-not $groq -or -not $gem) {
    Write-Host "`n== Två gratis nycklar behövs (2 min) ==" -ForegroundColor Cyan
    Write-Host "--- Nyckel 1 av 2: GROQ ---"
    Start-Process "https://console.groq.com/keys"
    $groq = Read-Host "  Logga in -> 'Create API Key' -> kopiera. Klistra in har och tryck Enter"
    Write-Host "--- Nyckel 2 av 2: GEMINI ---"
    Start-Process "https://aistudio.google.com/apikey"
    $gem = Read-Host "  Logga in -> 'Create API key' -> kopiera. Klistra in har och tryck Enter"
}

@"
GROQ_API_KEY=$groq
GEMINI_API_KEY=$gem
GROQ_MODEL=openai/gpt-oss-120b
GEMINI_MODEL=gemini-3.6-flash
EMBED_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
"@ | Set-Content -Encoding UTF8 ".env"

Write-Host "`nKlart! Startar IT-testare i bakgrunden..." -ForegroundColor Green
Start-Process -WindowStyle Hidden -FilePath "$dir\.venv\Scripts\uvicorn.exe" `
    -ArgumentList "app.main:app --host 127.0.0.1 --port 8765" -WorkingDirectory $dir
Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:8765"

# Genvagar (skrivbord + startmeny)
try {
    $ws = New-Object -ComObject WScript.Shell
    $targets = @(([Environment]::GetFolderPath('Desktop')),
                 (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'))
    foreach ($t in $targets) {
        if (-not (Test-Path $t)) { continue }
        $lnk = Join-Path $t 'IT-testare.lnk'
        $sc = $ws.CreateShortcut($lnk)
        $sc.TargetPath = "$dir\start.vbs"
        $sc.WorkingDirectory = $dir
        $sc.IconLocation = "$dir\web\icon.ico"
        $sc.Description = 'IT-testare - lokal AI for IT-test'
        $sc.Save()
    }
    Write-Host "Genvagar skapade: skrivbord + Startmeny ('IT-testare')." -ForegroundColor Green
} catch {
    Write-Host "Kunde inte skapa genvag automatiskt: $_" -ForegroundColor Yellow
    Write-Host "Starta istallet genom att dubbelklicka pa start.cmd i mappen it-testare."
}

Write-Host "`nKLART! Du kan stanga det har PowerShell-fonstret."
Write-Host "Nasta gang: dubbelklicka 'IT-testare' pa skrivbordet eller i Startmenyn." -ForegroundColor Green
