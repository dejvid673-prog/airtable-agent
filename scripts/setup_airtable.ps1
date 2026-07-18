param(
    [string]$Profile
)

$ErrorActionPreference = "Stop"
if (-not (Get-Command airtable-mcp -ErrorAction SilentlyContinue)) {
    throw "Brak airtable-mcp. Uruchom wcześniej .\scripts\bootstrap.ps1"
}

if ($Profile) {
    airtable-mcp configure --profile $Profile
    airtable-mcp whoami --profile $Profile
    airtable-mcp tools --profile $Profile --refresh
} else {
    airtable-mcp configure
    airtable-mcp whoami
    airtable-mcp tools --refresh
}

$Python = Join-Path (Split-Path -Parent $PSScriptRoot) ".venv\Scripts\python.exe"
$DoctorArgs = @("-m", "airtable_workbook_agent", "doctor", "--require-write")
if ($Profile) { $DoctorArgs += @("--profile", $Profile) }
& $Python @DoctorArgs
