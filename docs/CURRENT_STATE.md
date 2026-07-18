# Current state

Wersja: `0.1.0`

## Zaimplementowane
- kontrakt 11 kolumn produktowych;
- audyt braków, unikalności, EAN, cen, wag, stanów i wariantów;
- wykrywanie niezgodności dokumentacji arkuszy;
- generowanie `EXPORT_GOTOWY` i trzech arkuszy kontrolnych;
- ochrona pliku wejściowego przez SHA-256;
- raporty JSON/Markdown;
- testy jednostkowe oraz opcjonalny test integracyjny;
- oficjalny skill `airtable-overview` v1.0.0;
- oficjalny skill `airtable-filters` v1.0.0;
- przypięte źródło, commit, blob SHA i licencja skilli;
- test integralności niezmodyfikowanych plików upstream.

## Cel kolejnego audytu
Ocenić reguły na finalnym pliku oraz sposób rzeczywistego ładowania skilli przez
wybranego klienta agenta. Dopiero później rozszerzyć kontrakt, dodać bezpośredni
etap Airtable albo lokalny backend niezależny od środowiska OpenAI.
