#requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$RequireWrite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$TokenFile = Join-Path $Root ".secrets\airtable-token.dpapi"

if (-not (Test-Path $Python)) {
    throw "Virtual environment was not found. Run .\scripts\bootstrap.ps1 first."
}
if (-not (Test-Path $TokenFile)) {
    throw "Encrypted Airtable token was not found. Run .\scripts\setup_airtable_rest.ps1 first."
}

. (Join-Path $PSScriptRoot "_airtable_rest_token.ps1")
$env:AIRTABLE_TOKEN = Get-AirtableRestToken -TokenFile $TokenFile
try {
    $Arguments = @("-m", "airtable_workbook_agent", "doctor", "--backend", "rest")
    if ($RequireWrite) {
        $Arguments += "--require-write"
    }
    & $Python @Arguments
    exit $LASTEXITCODE
}
finally {
    Remove-Item Env:AIRTABLE_TOKEN -ErrorAction SilentlyContinue
}
