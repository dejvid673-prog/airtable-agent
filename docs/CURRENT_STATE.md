# Current state

Wersja robocza: `0.2.1`

## Gotowe

- lokalny backend XLSX oparty na `openpyxl`;
- uruchamianie na Windows bez `artifact_tool`;
- ujednolicanie nazw i rozdzielanie miar;
- mapowanie do trzech kategorii głównych;
- zachowanie wejścia i weryfikacja ID/SKU;
- domyślny backend Airtable Web API (REST) bez Node.js;
- opcjonalny backend `@airtable/mcp-cli`;
- token REST szyfrowany lokalnie przez Windows DPAPI;
- diagnostyka PAT bez wykonywania zapisu;
- podgląd create/update/unchanged/conflict/blocked;
- plan z SHA-256;
- ręczne zatwierdzenie przed zapisem;
- zapis create/update w partiach maksymalnie 10;
- brak delete i brak modyfikacji schematu;
- oficjalne skille Airtable;
- testy jednostkowe i integracyjne obu transportów.

## Zweryfikowane

- 865 rekordów wejściowych i wynikowych na przykładowym XLSX;
- zachowane ID i SKU;
- wyłącznie trzy kategorie główne;
- poprawne odfiltrowanie technicznych kodów rozmiaru;
- brak zmian pliku wejściowego;
- Linux CI: success;
- Windows PowerShell CI: success;
- DPAPI token round-trip: success;
- Airtable REST request/preview/apply tests: success.

## Dlaczego REST jest domyślny

Na komputerze użytkownika `@airtable/mcp-cli` 0.2.5 i 0.2.6 kończył handshake błędem `fetch failed`, mimo poprawnego DNS, TCP 443, TLS i bezpośredniego Node fetch. Agent nie jest już zależny od tego transportu.

## Do audytu produkcyjnego

- konfiguracja PAT przez `scripts/setup_airtable.ps1`;
- mapowanie finalnej bazy, tabeli i pól Airtable;
- rzeczywisty test READ_ONLY na koncie użytkownika;
- kontrolowany test zapisu na testowej tabeli;
- przegląd wyników przed scaleniem PR.
