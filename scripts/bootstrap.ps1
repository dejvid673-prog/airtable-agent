#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$PythonCommand = "py",
    [switch]$InstallAirtableCli,
    [switch]$SkipAirtableCli,
    [switch]$InstallCodexPlugin,
    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

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

if (-not (Get-Command $PythonCommand -ErrorAction SilentlyContinue)) {
    throw "Python launcher was not found: $PythonCommand"
}

if (-not (Test-Path ".venv")) {
    if ($PythonCommand -eq "py") {
        & $PythonCommand -3.12 -c "import sys" *> $null
        if ($LASTEXITCODE -eq 0) {
            Invoke-NativeCommand -FilePath $PythonCommand -ArgumentList @("-3.12", "-m", "venv", ".venv")
        } else {
            Invoke-NativeCommand -FilePath $PythonCommand -ArgumentList @("-3", "-m", "venv", ".venv")
        }
    } else {
        Invoke-NativeCommand -FilePath $PythonCommand -ArgumentList @("-m", "venv", ".venv")
    }
}

$Python = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment was not created correctly: $Python"
}

Invoke-NativeCommand -FilePath $Python -ArgumentList @("-m", "pip", "install", "--upgrade", "pip")
Invoke-NativeCommand -FilePath $Python -ArgumentList @("-m", "pip", "install", "-e", ".")

# REST is the default backend and does not require Node/npm. MCP CLI is optional.
if ($InstallAirtableCli -and -not $SkipAirtableCli) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "npm was not found. Install Node.js LTS or omit -InstallAirtableCli."
    }
    Invoke-NativeCommand -FilePath "npm" -ArgumentList @("install", "-g", "@airtable/mcp-cli@0.2.5")
}

if ($InstallCodexPlugin) {
    if (Get-Command codex -ErrorAction SilentlyContinue) {
        Invoke-NativeCommand -FilePath "codex" -ArgumentList @("plugin", "add", "airtable@openai-curated")
    } else {
        Write-Warning "The codex command was not found. The plugin was not installed."
    }
}

if (-not $SkipTests) {
    Invoke-NativeCommand -FilePath $Python -ArgumentList @("-m", "unittest", "discover", "-s", "tests", "-v")
}

Write-Host "Installation completed. Next run .\scripts\setup_airtable.ps1"
