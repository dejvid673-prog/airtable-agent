param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [string]$OutputFile,
    [string]$RunDirectory
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Brak środowiska .venv. Uruchom .\scripts\bootstrap.ps1" }
if (-not (Test-Path $InputFile)) { throw "Nie znaleziono pliku wejściowego: $InputFile" }

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $OutputFile) { $OutputFile = Join-Path $Root "data\output\produkty-przygotowane-$Stamp.xlsx" }
if (-not $RunDirectory) { $RunDirectory = Join-Path $Root "runs\prepare-$Stamp" }

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputFile) | Out-Null
New-Item -ItemType Directory -Force -Path $RunDirectory | Out-Null

& $Python -m airtable_workbook_agent prepare --input $InputFile --output $OutputFile --run-dir $RunDirectory
& $Python -m airtable_workbook_agent verify --input $InputFile --output $OutputFile
Write-Host "Wynik: $OutputFile"
Write-Host "Raport: $RunDirectory"
