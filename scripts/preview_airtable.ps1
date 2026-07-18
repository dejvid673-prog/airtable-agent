#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [Parameter(Mandatory = $true)][string]$MappingFile,
    [string]$PlanFile,
    [string]$ApprovalFile,
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
if (-not (Test-Path $InputFile)) { throw "Input file was not found: $InputFile" }
if (-not (Test-Path $MappingFile)) { throw "Mapping file was not found: $MappingFile" }

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $PlanFile) { $PlanFile = Join-Path $Root "runs\airtable-plan-$Stamp.json" }
if (-not $ApprovalFile) { $ApprovalFile = Join-Path $Root "approvals\airtable-approval-$Stamp.json" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $PlanFile) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ApprovalFile) | Out-Null

$Arguments = @(
    "-m", "airtable_workbook_agent", "airtable-preview",
    "--input", $InputFile,
    "--mapping", $MappingFile,
    "--plan", $PlanFile,
    "--approval-template", $ApprovalFile,
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

Write-Host "Plan: $PlanFile"
Write-Host "Approval: $ApprovalFile"
