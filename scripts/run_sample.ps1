param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [string]$OutputFile,
    [string]$RunDirectory
)

& (Join-Path $PSScriptRoot "prepare_workbook.ps1") `
  -InputFile $InputFile `
  -OutputFile $OutputFile `
  -RunDirectory $RunDirectory
