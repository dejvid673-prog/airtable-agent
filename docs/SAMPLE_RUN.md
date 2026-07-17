# Przykładowe uruchomienie

Przetestowano wersję `0.1.0` na przykładowym skoroszycie produktowym.
Rzeczywisty plik i dane rekordów nie są przechowywane w repozytorium.

## Struktura wejścia

- arkusz źródłowy: `EXPORT`;
- rekordy: 865;
- kolumny: 11;
- dodatkowy arkusz pomocniczy: `DANE_POMOCNICZE`.

## Wynik audytu

- `ERROR`: 7;
- `WARNING`: 97;
- `REVIEW`: 253;
- `INFO`: 368;
- automatyczne zmiany danych produktu: 0.

Agent prawidłowo odmówił automatycznej korekty niejednoznacznych danych.
Utworzył arkusz przygotowany oraz listę przypadków do weryfikacji.

## Weryfikacja

- plik wejściowy pozostał bez zmian;
- zachowano 865 z 865 rekordów;
- nagłówki są identyczne;
- kolejność ID produktu jest identyczna;
- kolejność SKU jest identyczna;
- wszystkie arkusze wynikowe zostały utworzone;
- drugi przebieg dał identyczne wartości w `EXPORT_GOTOWY`.
