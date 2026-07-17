# Architektura

Agent składa się z czterech warstw:

1. **Instrukcje agenta** — `AGENTS.md` i `agent/AGENT.md`.
2. **Kontrakt danych** — jawne reguły pliku produktowego.
3. **Deterministyczny silnik** — reguły w `rules.py` i runtime XLSX.
4. **Dowody wykonania** — JSON, Markdown, plik wynikowy i weryfikacja.

Model AI wybiera i uruchamia procedurę, ale nie wykonuje swobodnych zmian w
komórkach. Operacje są ograniczone kontraktem oraz kodem.
