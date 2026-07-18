from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import Finding


_SPACE_RE = re.compile(r"\s+")
PIPE_SPLIT_RE = re.compile(r"\s*\|\s*")
WEIGHT_RE = re.compile(r"(?<![\d.,])(\d+(?:[.,]\d+)?)\s*(kg|g|mg)\b", re.IGNORECASE)
VOLUME_RE = re.compile(r"(?<![\d.,])(\d+(?:[.,]\d+)?)\s*(ml|l)\b", re.IGNORECASE)
QUANTITY_RE = re.compile(r"(?<!\d)(\d+)\s*(szt\.?|sztuk|opak\.?|op\.?)(?!\w)", re.IGNORECASE)
RANGE_LENGTH_RE = re.compile(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*[-–]\s*(\d+(?:[.,]\d+)?)\s*(mm|cm|m)\b", re.IGNORECASE)
SINGLE_LENGTH_RE = re.compile(r"(?<![\d.,])(\d+(?:[.,]\d+)?)\s*(mm|cm|m)\b", re.IGNORECASE)


PREPARED_HEADERS = [
    "ID produktu", "SKU", "Nazwa produktu", "Kategoria główna", "Podkategoria",
    "Rozmiar / długość", "Pojemność", "Ilość", "Waga produktu kg",
    "Waga wysyłkowa kg", "Wariant wagowy", "Wytrzymałość kg",
    "Ciężar elementu", "Parametry dodatkowe", "Cena netto", "Stan",
    "Aktywny", "EAN", "Status agenta", "Uwagi agenta",
]


@dataclass(frozen=True)
class TransformResult:
    headers: list[str]
    rows: list[list[Any]]
    findings: list[Finding]
    metrics: dict[str, Any]
    category_map: list[list[Any]]


def normalize_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.replace("\u00a0", " ").replace("—", "–")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s*\|\s*", " | ", text)
    text = _SPACE_RE.sub(" ", text).strip(" |")
    return text


def _number(text: str) -> float:
    try:
        return float(Decimal(text.replace(",", ".")))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Niepoprawna liczba: {text}")


def _kg(value: float, unit: str) -> float:
    unit = unit.casefold()
    if unit == "kg":
        return value
    if unit == "g":
        return value / 1000
    return value / 1_000_000


def _token(value: float, unit: str) -> str:
    rendered = f"{value:g}".replace(".", ",")
    return f"{rendered} {unit.lower()}"


def _unique_join(values: list[str]) -> str | None:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            output.append(value)
    return " | ".join(output) if output else None


def _extract_measurements(name: str, variant: str | None, subcategory: str) -> dict[str, Any]:
    source_parts = PIPE_SPLIT_RE.split(normalize_text(name))
    base_name = source_parts[0] if source_parts else normalize_text(name)
    measure_text = " | ".join(part for part in [*source_parts[1:], normalize_text(variant) if variant else None] if part)

    raw_weights = [(m.group(0), _number(m.group(1)), m.group(2).lower()) for m in WEIGHT_RE.finditer(measure_text)]
    weights: list[tuple[str, float, str]] = []
    seen_weights: set[tuple[float, str]] = set()
    for raw, number, unit in raw_weights:
        key = (round(number, 9), unit)
        if key not in seen_weights:
            seen_weights.add(key)
            weights.append((raw, number, unit))
    volumes = [_token(_number(m.group(1)), m.group(2)) for m in VOLUME_RE.finditer(measure_text)]
    quantities = [f"{m.group(1)} szt." for m in QUANTITY_RE.finditer(measure_text)]
    range_matches = list(RANGE_LENGTH_RE.finditer(measure_text))
    ranges = [f"{m.group(1).replace('.', ',')}-{m.group(2).replace('.', ',')} {m.group(3).lower()}" for m in range_matches]
    technical_codes = {
        f"{m.group(1).replace(',', '').replace('.', '')}{m.group(2).replace(',', '').replace('.', '')}"
        for m in range_matches if m.group(3).lower() == "cm"
    }

    scrubbed = RANGE_LENGTH_RE.sub(" ", measure_text)
    lengths: list[str] = []
    for match in SINGLE_LENGTH_RE.finditer(scrubbed):
        raw_number = match.group(1).replace(",", ".")
        unit = match.group(2).lower()
        normalized_integer = raw_number[:-2] if raw_number.endswith(".0") else raw_number
        if unit == "cm" and normalized_integer in technical_codes:
            continue
        lengths.append(_token(_number(match.group(1)), match.group(2)))
    length_values = ranges + lengths

    category = subcategory.casefold()
    product_weights: list[tuple[str, float]] = []
    strength_values: list[float] = []
    component_weights: list[str] = []

    for raw, number, unit in weights:
        kg_value = _kg(number, unit)
        if "żyłki" in category or "plecion" in category:
            if unit == "kg":
                strength_values.append(number)
            else:
                component_weights.append(_token(number, unit))
        elif any(word in category for word in ("sprzęt wędkarski", "akcesoria wędkarskie", "przypony i haki")) and unit in {"g", "mg"}:
            component_weights.append(_token(number, unit))
        else:
            product_weights.append((_token(number, unit), kg_value))

    consumed_patterns = [WEIGHT_RE, VOLUME_RE, QUANTITY_RE, RANGE_LENGTH_RE, SINGLE_LENGTH_RE]
    extras = measure_text
    for pattern in consumed_patterns:
        extras = pattern.sub(" ", extras)
    extras = re.sub(r"[|/;,]+", " ", extras)
    extras = _SPACE_RE.sub(" ", extras).strip()
    if not extras or not re.search(r"[\wĄĆĘŁŃÓŚŹŻąćęłńóśźż]", extras):
        extras = ""

    weight_tokens = [item[0] for item in product_weights]
    weight_kg = product_weights[0][1] if len(product_weights) == 1 else None
    return {
        "base_name": base_name,
        "length": _unique_join(length_values),
        "volume": _unique_join(volumes),
        "quantity": _unique_join(quantities),
        "product_weight_kg": round(weight_kg, 6) if weight_kg is not None else None,
        "weight_variant": _unique_join(weight_tokens),
        "strength_kg": max(strength_values) if strength_values else None,
        "component_weight": _unique_join(component_weights),
        "extra": extras or None,
        "ambiguous_weight": len(product_weights) > 1,
    }


def _map_category(main: str, sub: str, mapping: dict[str, str]) -> tuple[str, str]:
    if sub not in mapping:
        raise KeyError(sub)
    return mapping[sub], sub


def transform_rows(headers: list[str], data_rows: list[list[Any]], contract: dict[str, Any]) -> TransformResult:
    index = {name: pos for pos, name in enumerate(headers)}
    missing = [name for name in contract["required_columns"] if name not in index]
    if missing:
        findings = [Finding("BLOCKER", "MISSING_COLUMN", 1, name, f"Brak wymaganej kolumny: {name}") for name in missing]
        return TransformResult(PREPARED_HEADERS, [], findings, {"records": len(data_rows), "blockers": len(missing)}, [])

    mapping: dict[str, str] = contract["category_mapping"]
    weight_optional = set(contract.get("weight_optional_subcategories", []))
    prepared: list[list[Any]] = []
    findings: list[Finding] = []
    category_counts: Counter[tuple[str, str]] = Counter()
    metrics = Counter()

    for excel_row, raw in enumerate(data_rows, start=2):
        row = dict(zip(headers, raw))
        old_name = normalize_text(row.get("Nazwa produktu") or "")
        sub = normalize_text(row.get("Podkategoria") or "")
        try:
            new_main, new_sub = _map_category(normalize_text(row.get("Kategoria główna") or ""), sub, mapping)
        except KeyError:
            new_main, new_sub = "", sub
            findings.append(Finding(
                "BLOCKER", "UNMAPPED_SUBCATEGORY", excel_row, "Podkategoria",
                "Podkategoria nie ma mapowania do jednej z trzech kategorii głównych.", sub,
                suggested_action="Dodaj podkategorię do category_mapping w kontrakcie.",
            ))

        measures = _extract_measurements(old_name, row.get("Rozmiar / wariant"), sub)
        normalized_name = normalize_text(measures["base_name"])
        if normalized_name != old_name:
            metrics["names_normalized"] += 1

        existing_shipping = row.get("Waga kg")
        shipping_weight = existing_shipping if isinstance(existing_shipping, (int, float)) and not isinstance(existing_shipping, bool) and existing_shipping > 0 else None
        product_weight = measures["product_weight_kg"]
        if shipping_weight is None and product_weight is not None and sub not in weight_optional:
            shipping_weight = round(product_weight * float(contract.get("shipping_weight_multiplier", 1.10)), 3)
            metrics["shipping_weights_added"] += 1
        if shipping_weight is not None and product_weight is not None and shipping_weight + 1e-9 < product_weight:
            findings.append(Finding(
                "WARNING", "SHIPPING_WEIGHT_BELOW_PRODUCT_WEIGHT", excel_row, "Waga kg",
                "Waga wysyłkowa jest mniejsza niż waga produktu wydzielona z nazwy.",
                shipping_weight, suggested_action="Zweryfikuj wagę opakowania i wartość w sklepie.",
            ))

        notes: list[str] = []
        if measures["ambiguous_weight"]:
            notes.append("Wykryto kilka wartości wagowych; wymaga kontroli.")
            findings.append(Finding(
                "REVIEW", "MULTIPLE_PRODUCT_WEIGHTS", excel_row, "Nazwa produktu",
                "W nazwie lub wariancie występuje kilka możliwych wag produktu.", old_name,
                suggested_action="Wybierz właściwą wagę wariantu.",
            ))
        if not new_main:
            notes.append("Brak mapowania kategorii.")

        status = "DO WERYFIKACJI" if notes or not new_main else "OK"
        category_counts[(new_main or "NIEZMAPOWANA", new_sub)] += 1
        metrics["records"] += 1
        if measures["length"]:
            metrics["length_extracted"] += 1
        if measures["volume"]:
            metrics["volume_extracted"] += 1
        if measures["quantity"]:
            metrics["quantity_extracted"] += 1
        if product_weight is not None:
            metrics["product_weight_extracted"] += 1
        if measures["strength_kg"] is not None:
            metrics["strength_extracted"] += 1
        if measures["component_weight"]:
            metrics["component_weight_extracted"] += 1

        prepared.append([
            row.get("ID produktu"), normalize_text(row.get("SKU")), normalized_name,
            new_main, new_sub, measures["length"], measures["volume"], measures["quantity"],
            product_weight, shipping_weight, measures["weight_variant"], measures["strength_kg"],
            measures["component_weight"], measures["extra"], row.get("Cena netto"),
            row.get("Stan"), row.get("Aktywny"), row.get("EAN"), status,
            " ".join(notes) or None,
        ])

    category_map = [[main, sub, count] for (main, sub), count in sorted(category_counts.items())]
    severity_counts = Counter(item.severity for item in findings)
    metrics["findings"] = len(findings)
    result_metrics = dict(metrics)
    result_metrics["severity_counts"] = dict(severity_counts)
    result_metrics["main_category_counts"] = dict(Counter(row[3] for row in prepared))
    return TransformResult(PREPARED_HEADERS, prepared, findings, result_metrics, category_map)
