# Airtable Product Workbook Preparation Agent

Jednozadaniowy agent przygotowujący produktowy skoroszyt XLSX do kontrolowanej
pracy lub importu w Airtable.

## Zakres wersji 0.1.0

Agent wykonuje zamknięty workflow:

```text
analyze → plan → apply → verify
```

- **analyze** — rozpoznaje strukturę i wykrywa problemy;
- **plan** — oddziela bezpieczne operacje od decyzji człowieka;
- **apply** — zapisuje nowy plik, nigdy nie nadpisuje wejścia;
- **verify** — porównuje wejście z wynikiem i potwierdza brak utraty rekordów.

Agent nie łączy się jeszcze bezpośrednio z Airtable i nie uruchamia się
automatycznie.

## Oficjalne skille Airtable

Repozytorium zawiera dwie niezmodyfikowane umiejętności z oficjalnego repozytorium
`Airtable/skills`:

- `skills/airtable-overview/SKILL.md` — model danych Airtable;
- `skills/airtable-filters/SKILL.md` — filtry rekordów dla Airtable MCP.

Oba skille mają wersję `1.0.0` i są przypięte do commita
`295ab93b7d765912ee1a0dc7f1abb0ecaf73f138`. Szczegóły pochodzenia i blob SHA
znajdują się w `skills/UPSTREAM.json`, a licencja w `THIRD_PARTY_NOTICES.md`.

## Wynik

W pliku wynikowym tworzone są arkusze:

- `EXPORT_GOTOWY` — przygotowana kopia danych źródłowych;
- `AUDYT_AGENTA` — podsumowanie kontroli;
- `DO_WERYFIKACJI` — wszystkie przypadki wymagające decyzji człowieka;
- `PLAN_ZMIAN` — wykonane i zablokowane operacje.

Arkusze wejściowe pozostają bez zmian.

## Uruchomienie w środowisku OpenAI Artifact Runtime

```powershell
python -m airtable_workbook_agent run `
  --input "data/input/produkty.xlsx" `
  --output "data/output/produkty_przygotowane.xlsx" `
  --run-dir "runs/run-001"
```

Runtime wymaga dostępu do pakietu `artifact_tool`, dostarczanego przez środowisko
narzędzi arkuszy OpenAI. Testy logiki biznesowej nie wymagają tego pakietu.

## Testy

```powershell
python -m unittest discover -s tests -v
```

## Bezpieczeństwo danych

Repozytorium jest publiczne. `.gitignore` blokuje rzeczywiste pliki XLSX,
katalogi wejściowe, wyjściowe, raporty uruchomień i zatwierdzenia.
