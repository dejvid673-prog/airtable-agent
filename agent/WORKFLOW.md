# Workflow

```text
INPUT XLSX
   ↓
analyze
   ├─ walidacja struktury
   ├─ braki i duplikaty
   ├─ EAN, ceny, wagi
   ├─ status/stan
   └─ zgodność dokumentacji z arkuszami
   ↓
plan
   ├─ bezpieczne normalizacje
   └─ decyzje człowieka
   ↓
apply
   ├─ kopia przygotowana
   ├─ arkusze audytu
   └─ brak zmian w źródle
   ↓
verify
   ├─ hash wejścia
   ├─ nagłówki
   ├─ rekordy
   ├─ ID/SKU
   └─ arkusze wynikowe
```
