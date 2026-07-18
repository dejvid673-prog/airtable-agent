#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [string]$OutputFile,
    [string]$RunDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList
    )

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $FilePath $($ArgumentList -join ' ')"
    }
}

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment was not found. Run .\scripts\bootstrap.ps1 first."
}
if (-not (Test-Path $InputFile)) {
    throw "Input file was not found: $InputFile"
}

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $OutputFile) {
    $OutputFile = Join-Path $Root "data\output\produkty-przygotowane-$Stamp.xlsx"
}
if (-not $RunDirectory) {
    $RunDirectory = Join-Path $Root "runs\prepare-$Stamp"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputFile) | Out-Null
New-Item -ItemType Directory -Force -Path $RunDirectory | Out-Null

Invoke-NativeCommand -FilePath $Python -ArgumentList @(
    "-m", "airtable_workbook_agent", "prepare",
    "--input", $InputFile,
    "--output", $OutputFile,
    "--run-dir", $RunDirectory
)
Invoke-NativeCommand -FilePath $Python -ArgumentList @(
    "-m", "airtable_workbook_agent", "verify",
    "--input", $InputFile,
    "--output", $OutputFile
)

Write-Host "Output: $OutputFile"
Write-Host "Report: $RunDirectory"
