#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Profile
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

if (-not (Get-Command airtable-mcp -ErrorAction SilentlyContinue)) {
    throw "airtable-mcp was not found. Run .\scripts\bootstrap.ps1 first."
}

if ($Profile) {
    Invoke-NativeCommand -FilePath "airtable-mcp" -ArgumentList @("configure", "--profile", $Profile)
    Invoke-NativeCommand -FilePath "airtable-mcp" -ArgumentList @("whoami", "--profile", $Profile)
    Invoke-NativeCommand -FilePath "airtable-mcp" -ArgumentList @("tools", "--profile", $Profile, "--refresh")
} else {
    Invoke-NativeCommand -FilePath "airtable-mcp" -ArgumentList @("configure")
    Invoke-NativeCommand -FilePath "airtable-mcp" -ArgumentList @("whoami")
    Invoke-NativeCommand -FilePath "airtable-mcp" -ArgumentList @("tools", "--refresh")
}

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment was not found. Run .\scripts\bootstrap.ps1 first."
}

$DoctorArgs = @("-m", "airtable_workbook_agent", "doctor", "--require-write")
if ($Profile) {
    $DoctorArgs += @("--profile", $Profile)
}
Invoke-NativeCommand -FilePath $Python -ArgumentList $DoctorArgs
