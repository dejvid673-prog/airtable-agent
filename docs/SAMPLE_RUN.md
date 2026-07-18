# Przykładowe uruchomienie 0.2.0

Test lokalnego backendu wykonano na przykładowym skoroszycie produktowym.

## Wejście

- 865 rekordów;
- 11 kolumn źródłowych;
- arkusze `EXPORT` i `DANE_POMOCNICZE`.

## Wynik

- 865 rekordów w `EXPORT_GOTOWY`;
- identyczna kolejność ID i SKU;
- dokładnie trzy kategorie główne;
- 389 rekordów z wydzieloną długością;
- 219 rekordów z wydzieloną pojemnością;
- 122 rekordy z wydzieloną ilością;
- 228 rekordów z jednoznaczną wagą produktu;
- techniczne kody typu `612 cm` i `2535 cm` odfiltrowane;
- plik wejściowy zachował SHA-256;
- `verification.passed=true`.

Test Airtable wykonuje się osobno na testowej tabeli po skonfigurowaniu PAT i lokalnego mapowania `fld...`.
