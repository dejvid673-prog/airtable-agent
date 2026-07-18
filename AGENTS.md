# AGENTS.md — Airtable Product Workbook Preparation Agent

## Cel repozytorium
Repozytorium zawiera jednego agenta wykonującego jedną pracę: przygotowanie
produktowego pliku XLSX do kontrolowanego użycia lub importu w Airtable.

## Zasady nadrzędne
1. Nigdy nie nadpisuj pliku wejściowego.
2. Rzeczywiste dane biznesowe nie mogą trafić do GitHub.
3. Najpierw wykonaj `analyze`, potem `plan`, dopiero następnie `apply` i `verify`.
4. Nie usuwaj ani nie scalaj rekordów automatycznie.
5. Nie poprawiaj ceny, EAN, SKU, nazwy, kategorii, wagi ani stanu, gdy reguła nie
   daje jednoznacznego wyniku.
6. Każda zmiana musi być widoczna w raporcie różnic.
7. Arkusz źródłowy pozostaje niezmieniony; przygotowane dane trafiają do
   `EXPORT_GOTOWY`.
8. Przypadki niejednoznaczne trafiają do `DO_WERYFIKACJI`.

## Oficjalne skille Airtable

Repozytorium zawiera przypięte, niezmodyfikowane skille z `Airtable/skills`:

- `skills/airtable-overview/SKILL.md` — model danych Airtable;
- `skills/airtable-filters/SKILL.md` — budowanie filtrów dla narzędzi Airtable MCP.

Przed operacją na bazach, tabelach, polach, rekordach, widokach lub interfejsach
przeczytaj `airtable-overview`. Przed wyszukiwaniem i filtrowaniem rekordów
przeczytaj `airtable-filters`. Skille nie zastępują kontraktu XLSX i nie mogą
rozszerzać zakresu wersji 0.1.0 o bezpośredni zapis do Airtable.

Źródło, wersje i blob SHA znajdują się w `skills/UPSTREAM.json`.

## Polecenia testowe
```powershell
python -m unittest discover -s tests -v
python -m airtable_workbook_agent --help
```

## Kryteria zakończenia
- wszystkie testy jednostkowe przechodzą;
- test integracyjny jest wykonany, gdy środowisko udostępnia `artifact_tool`;
- plik wejściowy zachowuje identyczny SHA-256;
- liczba rekordów i zestaw ID/SKU w `EXPORT_GOTOWY` odpowiadają źródłu;
- raport podaje wykonane, pominięte i zablokowane działania.
