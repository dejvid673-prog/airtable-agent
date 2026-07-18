param(
    [Parameter(Mandatory = $true)][string]$PlanFile,
    [Parameter(Mandatory = $true)][string]$ApprovalFile,
    [string]$ReportFile,
    [string]$Profile
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $ReportFile) { $ReportFile = Join-Path $Root "runs\airtable-execution-$Stamp.json" }

$Args = @("-m", "airtable_workbook_agent", "airtable-apply", "--plan", $PlanFile, "--approval", $ApprovalFile, "--report", $ReportFile)
if ($Profile) { $Args += @("--profile", $Profile) }
& $Python @Args
Write-Host "Raport wykonania: $ReportFile"
