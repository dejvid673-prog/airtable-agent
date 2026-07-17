# Current state

Wersja: `0.1.0`

## Zaimplementowane
- kontrakt 11 kolumn produktowych;
- audyt braków, unikalności, EAN, cen, wag, stanów i wariantów;
- wykrywanie niezgodności dokumentacji arkuszy;
- generowanie `EXPORT_GOTOWY` i trzech arkuszy kontrolnych;
- ochrona pliku wejściowego przez SHA-256;
- raporty JSON/Markdown;
- testy jednostkowe oraz opcjonalny test integracyjny.

## Cel kolejnego audytu
Ocenić reguły na finalnym pliku i dopiero wtedy rozszerzyć kontrakt lub dodać
lokalny backend niezależny od środowiska OpenAI.
