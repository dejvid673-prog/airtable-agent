# Pełny audyt repozytorium dla Codexa

Przeprowadź niezależny, rygorystyczny audyt całego repozytorium `airtable-agent`. Nie zakładaj, że obecna implementacja, dokumentacja ani testy są poprawne tylko dlatego, że CI przechodzi.

## Cel

Znajdź błędy logiczne, integracyjne, bezpieczeństwa, architektoniczne, platformowe i dokumentacyjne. Następnie zaproponuj poprawki oraz kolejność ich wdrożenia.

## Obowiązkowy zakres

1. Przeczytaj wszystkie pliki, zaczynając od:
   - `AGENTS.md`;
   - `agent/AGENT.md`;
   - `agent/WORKFLOW.md`;
   - `docs/*`;
   - `contracts/*`;
   - `skills/*/SKILL.md`;
   - całego `src/`, `scripts/` i `tests/`.
2. Uruchom:
   - kompilację Pythona;
   - wszystkie testy;
   - parser wszystkich skryptów PowerShell 5.1;
   - statyczną analizę typów i kodu, jeśli narzędzia są dostępne.
3. Sprawdź zgodność z aktualnym Airtable Web API i oficjalnym Airtable MCP/CLI na podstawie dokumentacji źródłowej.
4. Zweryfikuj działanie na Windows PowerShell 5.1 oraz PowerShell 7.
5. Nie używaj prawdziwych tokenów ani danych produkcyjnych. Do testów zapisu użyj wyłącznie atrap albo testowej bazy po osobnym zatwierdzeniu użytkownika.

## Znane objawy wymagające szczególnej analizy

- `@airtable/mcp-cli` 0.2.5 i 0.2.6 zwracał na Windows/Node 24 `TypeError: fetch failed`, mimo działającego DNS, TCP 443, TLS i bezpośredniego `fetch()`.
- Backend REST poprawnie uwierzytelniał PAT przez `/meta/whoami`, ale implementacja błędnie uznawała brak pola `scopes` za brak zakresów PAT.
- Skrypt ukrytego wejścia PowerShell przy wklejaniu PAT odbierał czasami jeden znak; dodano tryb `-FromClipboard`.
- Czyszczenie schowka przez `Set-Clipboard -Value ""` generowało błąd.
- Dokumentacja w części miejsc nadal może opisywać MCP jako główny backend mimo przejścia na REST.
- Nazwy wersji `0.2.0` i `0.2.1` mogą być niespójne między kodem, pakietem i dokumentacją.

## Obszary krytyczne

### Bezpieczeństwo

- wyciek tokenów w logach, wyjątkach, raportach lub planach;
- poprawność DPAPI i ograniczenie tokenu do bieżącego użytkownika;
- odporność planu i approval na podmianę ścieżek, TOCTOU i edycję po zatwierdzeniu;
- brak operacji delete i zmian schematu;
- poprawność limitów create/update;
- możliwość przypadkowego zapisu do niewłaściwej bazy lub tabeli.

### Airtable REST

- poprawność endpointów, parametrów i formatów odpowiedzi;
- PAT versus OAuth w `/meta/whoami`;
- wykrywanie realnych uprawnień przez operacje read-only zamiast niepewnego pola `scopes`;
- paginacja, offset, field IDs, `returnFieldsByFieldId` i limit 10 rekordów;
- obsługa 401, 403, 404, 422, 429 i 5xx;
- retry/backoff oraz częściowe powodzenie partii;
- typy pól Airtable, wartości select/link/checkbox/date i `typecast`.

### XLSX i dane produktowe

- utrata formuł, stylów, tabel, obrazów, nazwanych zakresów i właściwości pliku przez `openpyxl`;
- poprawność ekstrakcji kg/g/mg, l/ml, mm/cm/m, sztuk i zakresów;
- fałszywe interpretowanie wytrzymałości żyłki lub ciężaru elementu jako wagi produktu;
- zachowanie zer w SKU/EAN oraz typów liczbowych;
- duplikaty, puste wartości, nieznane kategorie i idempotencja kolejnego uruchomienia;
- zgodność finalnego pliku z wymaganiami importu Airtable.

### Kod i testy

- testy, które potwierdzają własne błędne założenia zamiast zachowania API;
- brak testów integracyjnych i przypadków negatywnych;
- błędne adnotacje typów, np. uzależnienie od konkretnej klasy transportu;
- martwy kod, duplikaty, niespójne nazwy i dokumentacja;
- poprawność kodów wyjścia CLI i wyjątków PowerShell.

## Format wyniku

Przygotuj raport zawierający:

1. **Podsumowanie wykonawcze** i ocenę gotowości produkcyjnej 0–100%.
2. **Listę ustaleń** posortowaną: BLOCKER, CRITICAL, HIGH, MEDIUM, LOW.
3. Dla każdego ustalenia:
   - plik i linie;
   - dowód lub sposób reprodukcji;
   - realny skutek;
   - konkretną poprawkę;
   - wymagany test regresyjny.
4. **Macierz wymagań versus implementacja**.
5. **Brakujące testy**.
6. **Plan napraw etapami**.
7. Oddzielną listę rzeczy, których nie udało się zweryfikować.

Nie scalaj PR, nie wykonuj force push i nie zapisuj do produkcyjnego Airtable. Najpierw przedstaw raport audytu.