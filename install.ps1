# TestARN - Windows-installation / uppdatering (alltid senaste versionen).
#   irm https://raw.githubusercontent.com/simonteklee/testarn/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

$repo = "simonteklee/testarn"
$dir = if ($env:TESTARN_DIR) { $env:TESTARN_DIR } else { "$HOME\testarn" }
# GitHub-API:t ger alltid färskt paket (ingen CDN-cache). Fallback: codeload.
$pkgApi = "https://api.github.com/repos/$repo/zipball/main"
$pkgUrl = "https://codeload.github.com/$repo/zip/refs/heads/main"
$verUrl = "https://api.github.com/repos/$repo/contents/version.txt?ref=main"

function Get-LatestVersion {
    try {
        return (Invoke-RestMethod -Uri $verUrl -Headers @{ "Cache-Control" = "no-cache"; "Accept" = "application/vnd.github.raw" } -UseBasicParsing).Trim()
    } catch { return "" }
}

function Get-Pkg {
    Remove-Item "$dir\_pkg.zip" -Force -ErrorAction SilentlyContinue
    try {
        Invoke-WebRequest -Uri $pkgApi -OutFile "$dir\_pkg.zip" -Headers @{ "Cache-Control" = "no-cache"; "User-Agent" = "testarn-installer" } -UseBasicParsing
    } catch {
        Invoke-WebRequest -Uri "$pkgUrl?t=$([int][double]::Parse((Get-Date -UFormat %s)))" -OutFile "$dir\_pkg.zip" -UseBasicParsing
    }
    Remove-Item "$dir\_pkg" -Recurse -Force -ErrorAction SilentlyContinue
    Expand-Archive -Path "$dir\_pkg.zip" -DestinationPath "$dir\_pkg" -Force
    $inner = (Get-ChildItem "$dir\_pkg" -Directory | Select-Object -First 1).FullName
    Get-ChildItem -Path $inner -Force | Move-Item -Destination $dir -Force
    Remove-Item "$dir\_pkg","$dir\_pkg.zip" -Recurse -Force
}

Write-Host "== TestARN installeras till $dir ==" -ForegroundColor Cyan

# 1) uv (fixar Python automatiskt)
if (-not (Get-Command uv -ErrorAction SilentlyContinue) -and -not (Test-Path "$HOME\.local\bin\uv.exe")) {
    Write-Host "• installerar uv..."
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
}
$env:Path = "$HOME\.local\bin;$env:Path"
$uv = if (Get-Command uv -ErrorAction SilentlyContinue) { "uv" } else { "$HOME\.local\bin\uv.exe" }

# 2) hamta programmet (senaste versionen)
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$latest = Get-LatestVersion
Write-Host "• hamtar programmet (senaste version$(if ($latest) { " $latest" }))..."
Get-Pkg
Set-Location $dir
$installed = (Get-Content version.txt -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
if ($latest -and $installed -ne $latest) {
    Write-Host "• fick version $installed, senaste ar $latest - hamtar en gang till..."
    Get-Pkg
    $installed = (Get-Content version.txt -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
}

# 3) miljo + paket
Write-Host "• installerar (tar ~1 min)..."
if (Test-Path ".venv") { Remove-Item ".venv" -Recurse -Force }
& $uv venv .venv
& $uv pip install -q -r requirements.txt

# 4) nycklar (behall befintliga om de finns)
$hasEnv = (Test-Path ".env") -and (Select-String -Path ".env" -Pattern "GROQ_API_KEY" -Quiet)
$groq = $env:GROQ_API_KEY; $gem = $env:GEMINI_API_KEY
if (-not $hasEnv -and (-not $groq -or -not $gem)) {
    Write-Host "`n== Tva gratis nycklar behovs (2 min) ==" -ForegroundColor Cyan
    Write-Host "--- Nyckel 1 av 2: GROQ ---"
    Start-Process "https://console.groq.com/keys"
    $groq = Read-Host "  Logga in -> 'Create API Key' -> kopiera. Klistra in har och tryck Enter"
    Write-Host "--- Nyckel 2 av 2: GEMINI ---"
    Start-Process "https://aistudio.google.com/apikey"
    $gem = Read-Host "  Logga in -> 'Create API key' -> kopiera. Klistra in har och tryck Enter"
}
if ($hasEnv -and (-not $groq -or -not $gem)) {
    Write-Host "• behaller dina befintliga nycklar i .env"
} elseif ($groq -and $gem) {
@"
GROQ_API_KEY=$groq
GEMINI_API_KEY=$gem
GROQ_MODEL=openai/gpt-oss-120b
GEMINI_MODEL=gemini-3.6-flash
EMBED_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
"@ | Set-Content -Encoding UTF8 ".env"
}

# 5) stoppa ev. gammal server sa att den NYA koden kor
Get-Process uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "`nKlart! TestARN version $installed$(if ($latest) { " (senaste: $latest)" }) - startar i bakgrunden..." -ForegroundColor Green
Start-Process -WindowStyle Hidden -FilePath "cmd.exe" -ArgumentList "/c","`"$dir\start-server.cmd`"" -WorkingDirectory $dir
# vanta tills servern svarar (max ~30 s); visa annars loggen
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 1000
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:8765/api/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { }
}
if (-not $ok) {
    Write-Host "! TestARN-servern startade inte." -ForegroundColor Red
    Write-Host "  Skicka denna loggfil till Simon: $dir\testarn.log" -ForegroundColor Red
    if (Test-Path "$dir\testarn.log") { Get-Content "$dir\testarn.log" -Tail 25 }
}
Start-Process "http://127.0.0.1:8765"

# 6) genvagar (skrivbord + startmeny)
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
    Write-Host "Starta istallet: dubbelklicka start.cmd i mappen testarn."
}

Write-Host "`nKLART! Du kan stanga det har PowerShell-fonstret." -ForegroundColor Green
Write-Host "Nasta gang: dubbelklicka 'TestARN' pa skrivbordet eller i Startmenyn."
