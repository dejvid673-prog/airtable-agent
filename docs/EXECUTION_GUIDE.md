# Instrukcja wykonania

## Instalacja

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\bootstrap.ps1
.\scripts\setup_airtable.ps1
```

## Diagnostyka

```powershell
.\.venv\Scripts\python.exe -m airtable_workbook_agent doctor --require-write
```

## Przygotowanie XLSX

```powershell
.\scripts\prepare_workbook.ps1 -InputFile "C:\Dane\produkty.xlsx"
```

## Mapowanie Airtable

1. W Airtable CLI odszukaj bazę i tabelę.
2. Pobierz schemat.
3. Skopiuj `contracts/airtable_mapping.example.json` do `contracts/airtable_mapping.local.json`.
4. Uzupełnij `app...`, `tbl...` oraz `fld...`.
5. Nie commituj pliku lokalnego.

Przykładowe polecenia:

```powershell
airtable-mcp search-bases --searchQuery "Produkty" -q
airtable-mcp list-tables-for-base --baseId appXXXXXXXX -q
airtable-mcp get-table-schema --input - -q
```

## Preview

```powershell
.\scripts\preview_airtable.ps1 `
  -InputFile "data\output\produkty_przygotowane.xlsx" `
  -MappingFile "contracts\airtable_mapping.local.json"
```

## Zatwierdzenie

Otwórz `approvals/airtable-approval.json`, sprawdź plan i ustaw:

```json
{
  "approved": true,
  "approved_by": "Gez"
}
```

Nie zmieniaj `plan_sha256` ani limitów bez ponownego wygenerowania planu.

## Apply

```powershell
.\scripts\apply_airtable.ps1 `
  -PlanFile "runs\airtable-plan.json" `
  -ApprovalFile "approvals\airtable-approval.json"
```
