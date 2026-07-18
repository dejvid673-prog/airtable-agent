param(
    [string]$PythonCommand = "py",
    [switch]$SkipAirtableCli,
    [switch]$InstallCodexPlugin
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".venv")) {
    & $PythonCommand -3.12 -m venv .venv
}

$Python = Join-Path $PWD ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -e .

if (-not $SkipAirtableCli) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "Brak npm. Zainstaluj Node.js LTS, a następnie uruchom skrypt ponownie."
    }
    npm install -g @airtable/mcp-cli
}

if ($InstallCodexPlugin) {
    if (Get-Command codex -ErrorAction SilentlyContinue) {
        codex plugin add airtable@openai-curated
    } else {
        Write-Warning "Nie znaleziono polecenia codex. Plugin nie został zainstalowany."
    }
}

& $Python -m unittest discover -s tests -v
Write-Host "Instalacja zakończona. Następnie uruchom .\scripts\setup_airtable.ps1"
