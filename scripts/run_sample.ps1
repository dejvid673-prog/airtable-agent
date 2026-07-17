param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [string]$OutputFile = "data/output/produkty_przygotowane.xlsx",
    [string]$RunDirectory = "runs/manual-run"
)

$ErrorActionPreference = "Stop"
python -m airtable_workbook_agent run `
  --input $InputFile `
  --output $OutputFile `
  --run-dir $RunDirectory

python -m airtable_workbook_agent verify `
  --input $InputFile `
  --output $OutputFile
