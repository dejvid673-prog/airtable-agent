# Decyzje architektoniczne

## ADR-001 — Oficjalny backend Airtable

Używamy `@airtable/mcp-cli`, a nie własnego klienta OAuth/API. CLI dynamicznie odkrywa aktualne narzędzia MCP i jest przeznaczone do skryptów oraz agentów.

## ADR-002 — Lokalny backend XLSX

Używamy `openpyxl`, aby agent działał lokalnie na Windowsie bez prywatnego runtime `artifact_tool`.

## ADR-003 — Preview przed zapisem

Każda synchronizacja najpierw generuje plan. Zapis wymaga oddzielnego pliku zatwierdzenia i zgodnego SHA-256.

## ADR-004 — Brak destructive operations

Agent nie usuwa rekordów, tabel, pól ani baz. Nie zmienia schematu.

## ADR-005 — Pole ID zamiast nazwy

Zapisy Airtable używają `fld...`, a aktualizacje `rec...`. Stabilny klucz produktu jest jawnie wskazany w lokalnym kontrakcie.

## ADR-006 — Dane poza GitHub

Tokeny, mapowania lokalne, XLSX, plany, zatwierdzenia i raporty pozostają poza publicznym repozytorium.
