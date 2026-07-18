# Airtable Product Workbook Agent

Agent przygotowuje produktowy skoroszyt XLSX, generuje kontrolowany plan synchronizacji i — dopiero po ręcznym zatwierdzeniu — tworzy lub aktualizuje rekordy w Airtable przez oficjalny `@airtable/mcp-cli`.

## Zakres wersji 0.2.0

```text
prepare XLSX → verify → Airtable preview → approval → Airtable apply
```

### Przygotowanie XLSX

Agent:

- ujednolica nazwy bez zgadywania treści produktu;
- rozdziela długość, pojemność, ilość, wagę produktu, wagę wysyłkową, wytrzymałość i ciężar elementu;
- mapuje istniejące podkategorie do dokładnie trzech kategorii głównych:
  - `Wędkarstwo`,
  - `Stawy i oczka wodne`,
  - `Ryby`;
- nie zmienia cen, stanów, aktywności ani EAN;
- nigdy nie nadpisuje wejścia;
- zachowuje oryginalne arkusze i dodaje arkusze wynikowe.

### Airtable

Agent używa oficjalnego CLI Airtable, które dynamicznie odkrywa aktualne narzędzia MCP. Tryb zapisu jest zabezpieczony planem SHA-256 oraz oddzielnym plikiem zatwierdzenia.

Agent nie usuwa rekordów i nie zmienia schematu bazy.

## Instalacja Windows

W PowerShell, w katalogu repozytorium:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\bootstrap.ps1
```

Skrypt tworzy `.venv`, instaluje pakiet Python oraz oficjalny `@airtable/mcp-cli`.

Następnie skonfiguruj Airtable:

```powershell
.\scripts\setup_airtable.ps1
```

## Przygotowanie pliku

```powershell
.\scripts\prepare_workbook.ps1 `
  -InputFile "C:\Dane\produkty.xlsx"
```

Wynik trafia do `data/output`, a raporty do `runs`.

## Podgląd synchronizacji Airtable

Najpierw skopiuj i uzupełnij:

```text
contracts/airtable_mapping.example.json
```

Następnie:

```powershell
.\scripts\preview_airtable.ps1 `
  -InputFile "data\output\produkty_przygotowane.xlsx" `
  -MappingFile "contracts\airtable_mapping.local.json"
```

Powstaną:

- plan synchronizacji JSON;
- szablon zatwierdzenia z `approved=false`.

## Zatwierdzony zapis

Po ręcznym sprawdzeniu planu ustaw w pliku zatwierdzenia:

```json
{
  "approved": true,
  "approved_by": "imię użytkownika"
}
```

Następnie:

```powershell
.\scripts\apply_airtable.ps1 `
  -PlanFile "runs\airtable-plan.json" `
  -ApprovalFile "approvals\airtable-approval.json"
```

## Diagnostyka

```powershell
.\.venv\Scripts\python.exe -m airtable_workbook_agent doctor --require-write
```

## Testy

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Oficjalne skille

Repo zawiera niezmodyfikowane, wersjonowane skille Airtable:

- `airtable-overview`;
- `airtable-filters`;
- `airtable-cli`.

Ich pochodzenie i blob SHA znajdują się w `skills/UPSTREAM.json`.
