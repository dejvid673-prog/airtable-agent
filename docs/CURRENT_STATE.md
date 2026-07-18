# Current state

Wersja: `0.2.0`

## Gotowe

- lokalny backend XLSX oparty na `openpyxl`;
- uruchamianie na Windows bez `artifact_tool`;
- ujednolicanie nazw i rozdzielanie miar;
- mapowanie do trzech kategorii głównych;
- zachowanie wejścia i weryfikacja ID/SKU;
- oficjalny backend Airtable `@airtable/mcp-cli`;
- diagnostyka auth/narzędzi;
- podgląd create/update/unchanged/conflict/blocked;
- plan z SHA-256;
- ręczne zatwierdzenie przed zapisem;
- zapis create/update w partiach maksymalnie 10;
- oficjalne skille Airtable;
- testy jednostkowe i integracyjne z atrapą CLI.

## Zweryfikowane na przykładowym pliku

- 865 rekordów wejściowych i wynikowych;
- zachowane ID i SKU;
- wyłącznie trzy kategorie główne;
- poprawne odfiltrowanie technicznych kodów rozmiaru;
- brak zmian pliku wejściowego.

## Do audytu produkcyjnego

- mapowanie finalnej bazy i tabeli Airtable;
- rzeczywisty test READ_ONLY na koncie użytkownika;
- rzeczywisty test zapisu na testowej tabeli;
- przegląd wyników przed scaleniem PR.
