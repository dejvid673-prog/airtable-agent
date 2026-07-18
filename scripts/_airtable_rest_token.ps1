#requires -Version 5.1
Set-StrictMode -Version Latest

function Get-AirtableRestToken {
    [CmdletBinding()]
    param(
        [string]$TokenFile = (Join-Path (Split-Path -Parent $PSScriptRoot) ".secrets\airtable-token.dpapi")
    )

    if ($env:AIRTABLE_TOKEN) {
        return $env:AIRTABLE_TOKEN
    }
    if (-not (Test-Path $TokenFile)) {
        throw "Encrypted Airtable token was not found. Run .\scripts\setup_airtable_rest.ps1 first."
    }

    $Encrypted = Get-Content -Raw -Path $TokenFile
    $SecureToken = ConvertTo-SecureString $Encrypted
    $Bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureToken)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
    }
}
