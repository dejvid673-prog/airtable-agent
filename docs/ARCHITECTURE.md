# Architektura

## Warstwy

1. **Agent i zasady** — `AGENTS.md`, `agent/AGENT.md`, `agent/WORKFLOW.md`.
2. **Skille Airtable** — model danych, filtry i oficjalny CLI.
3. **Kontrakty** — struktura produktu i lokalne mapowanie XLSX → Airtable field IDs.
4. **Lokalny silnik XLSX** — `openpyxl`, bez zależności od prywatnego runtime.
5. **Airtable MCP CLI** — oficjalny `@airtable/mcp-cli`, dynamiczne odkrywanie narzędzi.
6. **Warstwa synchronizacji** — preview, SHA-256 planu, approval, create/update.
7. **Dowody** — XLSX wynikowy, audit JSON/Markdown, plan, zatwierdzenie i raport wykonania.

## Granica odpowiedzialności

Model/agent wybiera workflow i interpretuje raporty. Kod deterministyczny wykonuje transformacje, porównania, limity i kontrolę zatwierdzenia.

## Brak własnego OAuth/API

Repo nie przechowuje tokenów i nie implementuje własnego klienta Airtable. Autoryzację i aktualny zestaw narzędzi zapewnia oficjalny CLI/MCP.
