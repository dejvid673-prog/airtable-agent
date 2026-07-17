# Decyzje architektoniczne

## ADR-001 — Jeden agent, jedna praca
Agent nie zarządza Airtable ani PrestaShop. Przygotowuje wyłącznie XLSX.

## ADR-002 — Źródło pozostaje bez zmian
Wynik powstaje w nowym pliku i nowym arkuszu `EXPORT_GOTOWY`.

## ADR-003 — Brak automatycznych decyzji biznesowych
Duplikaty nazw/EAN, zerowe ceny, podejrzane warianty i konflikty stanów są
raportowane, ale nie naprawiane bez potwierdzonej reguły.

## ADR-004 — Dane produkcyjne poza repozytorium
Repo publiczne przechowuje kod, kontrakty i syntetyczne testy, ale nie pliki
produktowe ani raporty wykonania.

## ADR-005 — Runtime 0.1.0
Integracja XLSX używa `artifact_tool` dostępnego w środowisku narzędzi arkuszy
OpenAI. Rdzeń reguł pozostaje niezależny i testowalny bez tego runtime.
