#requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$FromClipboard
)

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

$PlainToken = $null
$SecureToken = $null
try {
    if ($FromClipboard) {
        Write-Host "Reading the complete Airtable PAT from the Windows clipboard."
        $PlainToken = (Get-Clipboard -Raw).Trim()
        if (-not $PlainToken) {
            throw "The Windows clipboard is empty. Copy the complete Airtable PAT and run the command again."
        }
        $SecureToken = ConvertTo-SecureString $PlainToken -AsPlainText -Force
    }
    else {
        Write-Host "Paste the complete Airtable PAT. Input will remain hidden."
        Write-Host "The complete token must contain a dot and a long secret after the dot."
        $SecureToken = Read-Host "Token" -AsSecureString
        $Bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureToken)
        try {
            $PlainToken = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Bstr)
        }
        finally {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
        }
    }

    if ($PlainToken -notmatch '^pat[^\.\s]{4,}\.[^\s]{9,}$') {
        throw "The pasted value is not a complete Airtable PAT. Copy the full regenerated token, not the Token ID."
    }

    $Encrypted = ConvertFrom-SecureString $SecureToken
    Set-Content -Path $TokenFile -Value $Encrypted -Encoding ASCII

    . (Join-Path $PSScriptRoot "_airtable_rest_token.ps1")
    $env:AIRTABLE_TOKEN = Get-AirtableRestToken -TokenFile $TokenFile
    & $Python -m airtable_workbook_agent doctor --backend rest
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Validation failed. The encrypted token was preserved so the diagnostic can be repeated after correcting Airtable scopes."
        throw "REST validation failed. Read the JSON error shown above."
    }
    Write-Host "Airtable REST configuration completed."
    Write-Host "Encrypted token: $TokenFile"
}
finally {
    Remove-Item Env:AIRTABLE_TOKEN -ErrorAction SilentlyContinue
    $PlainToken = $null
    $SecureToken = $null
    if ($FromClipboard) {
        try {
            Set-Clipboard -Value "[cleared by airtable-agent]"
            Write-Host "Windows clipboard overwritten."
        }
        catch {
            Write-Warning "Could not overwrite the Windows clipboard automatically. Copy any harmless text manually."
        }
    }
}
