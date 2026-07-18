# Workflow agenta

## A. Pierwsza instalacja

1. Uruchom `scripts/bootstrap.ps1`.
2. Uruchom `scripts/setup_airtable.ps1`.
3. Wykonaj `doctor --require-write`.
4. Nie przechodź dalej, gdy brakuje narzędzi lub autoryzacji.

## B. Przygotowanie skoroszytu

1. Odczytaj kontrakt produktowy.
2. Oblicz SHA-256 wejścia.
3. Odczytaj arkusz `EXPORT`.
4. Zablokuj pracę przy brakujących kolumnach lub nieznanej podkategorii.
5. Ujednolić nazwy.
6. Wydzielić długość, pojemność, ilość, wagę produktu, wagę wysyłkową, wytrzymałość i ciężar elementu.
7. Zmapować podkategorie do trzech kategorii głównych.
8. Utworzyć `EXPORT_GOTOWY`, raport, mapę kategorii, plan i listę kontroli.
9. Zweryfikować liczbę rekordów, ID, SKU i kategorie.

## C. Odkrycie Airtable

1. Przeczytaj trzy skille Airtable.
2. Uruchom `airtable-mcp tools --json`.
3. Sprawdź poziom dostępu narzędzi.
4. Odszukaj bazę.
5. Pobierz listę tabel i schemat.
6. Zapisz lokalne mapowanie nazw kolumn XLSX do `fld...`.

## D. Podgląd synchronizacji

1. Odczytaj `EXPORT_GOTOWY`.
2. Pobierz rekordy z wymaganymi polami.
3. Porównaj po stabilnym kluczu.
4. Zablokuj brakujące i zduplikowane klucze.
5. Utwórz plan `create/update/unchanged/conflict/blocked`.
6. Oblicz SHA-256 planu.
7. Utwórz szablon zatwierdzenia z `approved=false`.
8. Zakończ bez zapisu.

## E. Zatwierdzony zapis

1. Zweryfikuj SHA-256 planu.
2. Zweryfikuj identyczny SHA w zatwierdzeniu.
3. Wymagaj `approved=true`.
4. Wymagaj braku konfliktów i rekordów zablokowanych.
5. Sprawdź limity create/update.
6. Wykonaj zapis partiami do 10 rekordów.
7. Zapisz raport wykonania.

## F. Audyt

Nie scalaj PR przed audytem kodu, kontraktów, testów i wyniku na testowej bazie Airtable.
