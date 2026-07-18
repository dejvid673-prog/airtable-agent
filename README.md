# Airtable Product Workbook Agent

Agent przygotowuje produktowy skoroszyt XLSX, generuje kontrolowany plan synchronizacji i — dopiero po ręcznym zatwierdzeniu — tworzy lub aktualizuje rekordy w Airtable.

## Workflow

```text
prepare XLSX → verify → Airtable preview → approval → Airtable apply
```

## Przygotowanie XLSX

Agent:

- ujednolica nazwy bez zgadywania treści produktu;
- rozdziela długość, pojemność, ilość, wagę produktu, wagę wysyłkową, wytrzymałość i ciężar elementu;
- mapuje istniejące podkategorie do dokładnie trzech kategorii głównych: `Wędkarstwo`, `Stawy i oczka wodne`, `Ryby`;
- nie zmienia cen, stanów, aktywności ani EAN;
- nigdy nie nadpisuje wejścia;
- zachowuje oryginalne arkusze i dodaje arkusze wynikowe.

## Airtable

Domyślnym transportem jest oficjalny Airtable Web API (`--backend rest`). Opcjonalnie można użyć oficjalnego `@airtable/mcp-cli` (`--backend mcp`). Oba transporty korzystają z tego samego mechanizmu bezpieczeństwa:

- preview bez zapisu;
- plan zabezpieczony SHA-256;
- oddzielny plik zatwierdzenia;
- limity create/update;
- partie maksymalnie 10 rekordów;
- brak delete;
- brak zmian schematu.

Token REST jest przechowywany lokalnie jako zaszyfrowany plik Windows DPAPI w `.secrets/` i nie trafia do Git.

## Instalacja Windows

W PowerShell, w katalogu repozytorium:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\bootstrap.ps1"
```

Skrypt tworzy `.venv`, instaluje pakiet Python i uruchamia testy. Node.js nie jest wymagany dla domyślnego backendu REST.

Opcjonalny MCP CLI:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\bootstrap.ps1" -InstallAirtableCli
```

## Konfiguracja Airtable REST

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\setup_airtable.ps1"
```

Wklej pełny PAT. Pole wejściowe pozostaje niewidoczne. Skrypt szyfruje token przez Windows DPAPI i wykonuje kontrolę read-only przez Airtable Web API.

## Przygotowanie pliku

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\prepare_workbook.ps1" -InputFile "C:\Dane\produkty.xlsx"
```

Wynik trafia do `data/output`, a raporty do `runs`.

## Podgląd synchronizacji Airtable

Skopiuj i uzupełnij `contracts/airtable_mapping.example.json` jako `contracts/airtable_mapping.local.json`, wpisując identyfikatory `app...`, `tbl...` i `fld...`.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\preview_airtable.ps1" -InputFile "data\output\produkty_przygotowane.xlsx" -MappingFile "contracts\airtable_mapping.local.json"
```

Powstaną plan synchronizacji JSON i szablon zatwierdzenia z `approved=false`.

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
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\apply_airtable.ps1" -PlanFile "runs\airtable-plan.json" -ApprovalFile "approvals\airtable-approval.json"
```

## Diagnostyka REST

Skrypty użytkownika automatycznie odszyfrowują token tylko na czas pojedynczego procesu. Ręczna diagnostyka wymaga ustawienia `AIRTABLE_TOKEN` w bieżącym procesie albo użycia `setup_airtable.ps1`.

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
