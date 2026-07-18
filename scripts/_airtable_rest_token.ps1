#requires -Version 5.1
Set-StrictMode -Version Latest

$script:AirtableAgentRoot = Split-Path -Parent $PSScriptRoot

function Get-AirtableRestToken {
    [CmdletBinding()]
    param(
        [string]$TokenFile
    )

    $EnvironmentToken = [Environment]::GetEnvironmentVariable("AIRTABLE_TOKEN", "Process")
    if (-not [string]::IsNullOrWhiteSpace($EnvironmentToken)) {
        return $EnvironmentToken
    }
    if ([string]::IsNullOrWhiteSpace($TokenFile)) {
        $TokenFile = Join-Path $script:AirtableAgentRoot ".secrets\airtable-token.dpapi"
    }
    if (-not (Test-Path $TokenFile)) {
        throw "Encrypted Airtable token was not found. Run .\scripts\setup_airtable_rest.ps1 first."
    }

    $Encrypted = (Get-Content -Raw -Path $TokenFile).Trim()
    $SecureToken = ConvertTo-SecureString $Encrypted
    $Bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureToken)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
    }
}
