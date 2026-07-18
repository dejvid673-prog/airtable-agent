#requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment was not found. Run .\scripts\bootstrap.ps1 first."
}

$SecretsDirectory = Join-Path $Root ".secrets"
$TokenFile = Join-Path $SecretsDirectory "airtable-token.dpapi"
New-Item -ItemType Directory -Force -Path $SecretsDirectory | Out-Null

Write-Host "Paste the complete Airtable PAT. Input will remain hidden."
$SecureToken = Read-Host "Token" -AsSecureString
$Encrypted = ConvertFrom-SecureString $SecureToken
Set-Content -Path $TokenFile -Value $Encrypted -Encoding ASCII

. (Join-Path $PSScriptRoot "_airtable_rest_token.ps1")
$env:AIRTABLE_TOKEN = Get-AirtableRestToken -TokenFile $TokenFile
try {
    & $Python -m airtable_workbook_agent doctor --backend rest
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -Force -ErrorAction SilentlyContinue $TokenFile
        throw "REST authentication failed. The encrypted token file was removed."
    }
    Write-Host "Airtable REST configuration completed."
    Write-Host "Encrypted token: $TokenFile"
}
finally {
    Remove-Item Env:AIRTABLE_TOKEN -ErrorAction SilentlyContinue
}
