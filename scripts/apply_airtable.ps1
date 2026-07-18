#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PlanFile,
    [Parameter(Mandatory = $true)][string]$ApprovalFile,
    [string]$ReportFile,
    [ValidateSet("rest", "mcp")][string]$Backend = "rest",
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

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Virtual environment was not found. Run .\scripts\bootstrap.ps1 first." }
if (-not (Test-Path $PlanFile)) { throw "Plan file was not found: $PlanFile" }
if (-not (Test-Path $ApprovalFile)) { throw "Approval file was not found: $ApprovalFile" }

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $ReportFile) { $ReportFile = Join-Path $Root "runs\airtable-execution-$Stamp.json" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ReportFile) | Out-Null

$Arguments = @(
    "-m", "airtable_workbook_agent", "airtable-apply",
    "--plan", $PlanFile,
    "--approval", $ApprovalFile,
    "--report", $ReportFile,
    "--backend", $Backend
)
if ($Backend -eq "mcp" -and $Profile) { $Arguments += @("--profile", $Profile) }

if ($Backend -eq "rest") {
    . (Join-Path $PSScriptRoot "_airtable_rest_token.ps1")
    $env:AIRTABLE_TOKEN = Get-AirtableRestToken
}
try {
    Invoke-NativeCommand -FilePath $Python -ArgumentList $Arguments
}
finally {
    if ($Backend -eq "rest") { Remove-Item Env:AIRTABLE_TOKEN -ErrorAction SilentlyContinue }
}

Write-Host "Execution report: $ReportFile"
