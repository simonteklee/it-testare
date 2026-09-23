# TestARN - Windows-installation (PowerShell).
#   irm https://raw.githubusercontent.com/simonteklee/it-testare/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

$dir = if ($env:IT_TESTARE_DIR) { $env:IT_TESTARE_DIR } else { "$HOME\it-testare" }
$pkgUrl = "https://codeload.github.com/simonteklee/it-testare/zip/refs/heads/main"

Write-Host "== TestARN installeras till $dir ==" -ForegroundColor Cyan

# 1) uv (fixar Python automatiskt)
if (-not (Get-Command uv -ErrorAction SilentlyContinue) -and -not (Test-Path "$HOME\.local\bin\uv.exe")) {
    Write-Host "• installerar uv..."
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
}
$env:Path = "$HOME\.local\bin;$env:Path"
$uv = if (Get-Command uv -ErrorAction SilentlyContinue) { "uv" } else { "$HOME\.local\bin\uv.exe" }

# 2) hamta programmet (från GitHub-repot)
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Write-Host "• hamtar programmet..."
Invoke-WebRequest -Uri $pkgUrl -OutFile "$dir\_pkg.zip"
Expand-Archive -Path "$dir\_pkg.zip" -DestinationPath "$dir\_pkg" -Force
$inner = (Get-ChildItem "$dir\_pkg" -Directory | Select-Object -First 1).FullName
Get-ChildItem -Path $inner -Force | Move-Item -Destination $dir -Force
Remove-Item "$dir\_pkg","$dir\_pkg.zip" -Recurse -Force
Set-Location $dir

# 3) miljo + paket
Write-Host "• installerar (tar ~1 min)..."
if (Test-Path ".venv") { Remove-Item ".venv" -Recurse -Force }
& $uv venv .venv
& $uv pip install -q -r requirements.txt

# 4) nycklar
$groq = $env:GROQ_API_KEY; $gem = $env:GEMINI_API_KEY
if (-not $groq -or -not $gem) {
    Write-Host "`n== Tva gratis nycklar behovs (2 min) ==" -ForegroundColor Cyan
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

Write-Host "`nKlart! Startar TestARN i bakgrunden..." -ForegroundColor Green
Start-Process -WindowStyle Hidden -FilePath "$dir\.venv\Scripts\uvicorn.exe" `
    -ArgumentList "app.main:app --host 127.0.0.1 --port 8765" -WorkingDirectory $dir
Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:8765"

# 5) genvagar (skrivbord + startmeny)
try {
    $ws = New-Object -ComObject WScript.Shell
    $targets = @(([Environment]::GetFolderPath('Desktop')),
                 (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'))
    foreach ($t in $targets) {
        if (-not (Test-Path $t)) { continue }
        $lnk = Join-Path $t 'TestARN.lnk'
        $sc = $ws.CreateShortcut($lnk)
        $sc.TargetPath = "$dir\start.vbs"
        $sc.WorkingDirectory = $dir
        $sc.IconLocation = "$dir\web\icon.ico"
        $sc.Description = 'TestARN - lokal AI for IT-test'
        $sc.Save()
    }
    Write-Host "Genvagar skapade: skrivbord + Startmeny ('TestARN')." -ForegroundColor Green
} catch {
    Write-Host "Kunde inte skapa genvag automatiskt: $_" -ForegroundColor Yellow
    Write-Host "Starta istallet: dubbelklicka start.cmd i mappen it-testare."
}

Write-Host "`nKLART! Du kan stanga det har PowerShell-fonstret." -ForegroundColor Green
Write-Host "Nasta gang: dubbelklicka 'TestARN' pa skrivbordet eller i Startmenyn."
