param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [Parameter(Mandatory = $true)][string]$MappingFile,
    [string]$PlanFile,
    [string]$ApprovalFile,
    [string]$Profile
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $PlanFile) { $PlanFile = Join-Path $Root "runs\airtable-plan-$Stamp.json" }
if (-not $ApprovalFile) { $ApprovalFile = Join-Path $Root "approvals\airtable-approval-$Stamp.json" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $PlanFile) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ApprovalFile) | Out-Null

$Args = @("-m", "airtable_workbook_agent", "airtable-preview", "--input", $InputFile, "--mapping", $MappingFile, "--plan", $PlanFile, "--approval-template", $ApprovalFile)
if ($Profile) { $Args += @("--profile", $Profile) }
& $Python @Args
Write-Host "Plan: $PlanFile"
Write-Host "Zatwierdzenie: $ApprovalFile"
