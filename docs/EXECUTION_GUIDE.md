# Instrukcja wykonania

## 1. Umieść plik lokalnie

```text
data/input/produkty.xlsx
```

Plik jest ignorowany przez Git.

## 2. Uruchom pełny workflow

```powershell
python -m airtable_workbook_agent run `
  --input "data/input/produkty.xlsx" `
  --output "data/output/produkty_przygotowane.xlsx" `
  --run-dir "runs/run-001"
```

## 3. Sprawdź wynik

```powershell
python -m airtable_workbook_agent verify `
  --input "data/input/produkty.xlsx" `
  --output "data/output/produkty_przygotowane.xlsx"
```

## 4. Odczytaj dowody

- `runs/run-001/audit.json`
- `runs/run-001/audit.md`
- `runs/run-001/plan.md`
- `runs/run-001/execution.json`
- `runs/run-001/verification.json`
