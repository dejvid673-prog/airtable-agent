# Runbook dla Codexa

Pracuj na bieżącej gałęzi repozytorium. Najpierw przeczytaj `AGENTS.md`, `agent/AGENT.md`, `agent/WORKFLOW.md` oraz trzy skille Airtable.

## Przygotowanie pliku

```text
Uruchom lokalny workflow prepare na pliku wskazanym przez użytkownika. Nie nadpisuj wejścia. Uruchom testy i verify. Podaj ścieżki do XLSX oraz raportów.
```

## Airtable READ_ONLY/PREVIEW

```text
Sprawdź połączenie Airtable MCP. Nie zakładaj baseId, tableId ani fieldId. Odszukaj bazę i tabelę, pobierz schemat, przygotuj lokalny kontrakt mapowania, a następnie wygeneruj wyłącznie plan synchronizacji. Nie wykonuj create ani update.
```

## Airtable APPROVED_WRITE

```text
Przeczytaj plan i plik zatwierdzenia. Zweryfikuj plan_sha256, approved=true, limity i brak konfliktów. Dopiero wtedy uruchom airtable-apply. Nie wykonuj delete ani zmian schematu. Zapisz raport.
```
