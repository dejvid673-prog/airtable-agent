# AGENTS.md — Airtable Product Workbook Agent

## Cel

Repozytorium zawiera jednego agenta realizującego kontrolowany proces:

```text
prepare XLSX → verify → Airtable preview → human approval → Airtable apply
```

## Obowiązkowe materiały

Przed pracą przeczytaj:

1. `agent/AGENT.md`;
2. `agent/WORKFLOW.md`;
3. `contracts/product_workbook_contract.json`;
4. `skills/airtable-overview/SKILL.md` przed interpretacją modelu Airtable;
5. `skills/airtable-filters/SKILL.md` przed filtrowaniem rekordów;
6. `skills/airtable-cli/SKILL.md` przed wywołaniem `airtable-mcp`.

## Zasady bezpieczeństwa

1. Nigdy nie nadpisuj wejściowego XLSX.
2. Nie umieszczaj rzeczywistych danych biznesowych, tokenów, planów ani raportów w GitHub.
3. Nie zakładaj `baseId`, `tableId`, `fieldId` ani nazw pól — użyj MCP/CLI do odkrycia schematu.
4. Domyślny tryb Airtable to READ_ONLY/PREVIEW.
5. Zapis jest dozwolony tylko dla planu z poprawnym SHA-256 i pliku zatwierdzenia z `approved=true`.
6. Nie usuwaj rekordów i nie zmieniaj schematu bazy.
7. Dziel zapis na partie maksymalnie 10 rekordów.
8. Przerwij przy duplikacie klucza, brakującym kluczu, nieznanej podkategorii lub niezgodności planu z zatwierdzeniem.
9. Nigdy nie loguj `AIRTABLE_TOKEN`.
10. Każda wykonana operacja musi mieć raport JSON.

## Testy obowiązkowe

```powershell
python -m compileall -q src tests
python -m unittest discover -s tests -v
```

Przed dopuszczeniem zapisu uruchom również:

```powershell
python -m airtable_workbook_agent doctor --require-write
```

## Definicja ukończenia

- testy przechodzą;
- lokalne przygotowanie XLSX działa bez `artifact_tool`;
- wejściowy SHA-256 pozostaje niezmieniony;
- plan Airtable powstaje bez zapisu;
- `airtable-apply` odrzuca brak zatwierdzenia i zmodyfikowany plan;
- PR pozostaje draftem do audytu człowieka.
