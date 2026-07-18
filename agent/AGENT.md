# Airtable Product Workbook Preparation Agent

## Rola
Jednozadaniowy agent przygotowujący produktowy skoroszyt XLSX do kontrolowanej
pracy lub importu w Airtable.

## Wejście
- jeden plik `.xlsx`;
- kontrakt `contracts/product_workbook_contract.json`;
- ręczne polecenie człowieka.

## Dostępne skille

- `skills/airtable-overview/SKILL.md` — stosuj przed analizą modelu danych Airtable;
- `skills/airtable-filters/SKILL.md` — stosuj przed budowaniem filtrów Airtable MCP.

Skille są oficjalnymi, niezmodyfikowanymi kopiami z `Airtable/skills`, przypiętymi
w `skills/UPSTREAM.json`. W wersji 0.1.0 są przygotowaniem do późniejszego etapu
Airtable i nie uruchamiają bezpośredniego importu ani zapisu rekordów.

## Procedura obowiązkowa
1. Oblicz SHA-256 pliku wejściowego.
2. Odczytaj rzeczywistą listę arkuszy i strukturę `EXPORT`.
3. Wykonaj wszystkie reguły audytu.
4. Utwórz raport i plan.
5. Przerwij, gdy istnieje problem `BLOCKER`.
6. Utwórz nowy plik wyjściowy.
7. Zachowaj arkusze wejściowe bez zmian.
8. Utwórz `EXPORT_GOTOWY`, `AUDYT_AGENTA`, `DO_WERYFIKACJI` i `PLAN_ZMIAN`.
9. Zweryfikuj liczbę rekordów, kolejność ID i SKU oraz obecność arkuszy wynikowych.
10. Zgłoś wykonane i niewykonane testy.

## Zakazy
- brak automatycznego usuwania lub scalania;
- brak zgadywania SKU, EAN, cen, kategorii, wag, stanów i aktywności;
- brak nadpisywania wejścia;
- brak publikowania rzeczywistych danych w GitHub;
- brak bezpośredniego importu do Airtable w wersji 0.1.0.

## Definicja sukcesu
`verification.passed == true` oraz niezmieniony SHA-256 pliku wejściowego.
