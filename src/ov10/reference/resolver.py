from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from ov10.domain import IngestionBundle, InstrumentType
from ov10.reference.models import InstrumentReference

UNKNOWN_CATEGORY = "unknown"
OBSERVED_REFERENCE_ORIGIN = "observed_canonical_facts"
IDENTITY_STATUS_OBSERVED = "observed_identity"
IDENTITY_STATUS_OBSERVED_CONFLICT = "observed_with_conflict"
IDENTITY_STATUS_OBSERVED_ONLY = "observed_only"


@dataclass(slots=True)
class _ObservedInstrument:
    instrument_type_counts: Counter[str] = field(default_factory=Counter)
    asset_category_counts: Counter[str] = field(default_factory=Counter)
    currency_counts: Counter[str] = field(default_factory=Counter)
    transaction_count: int = 0
    dividend_receipt_count: int = 0
    corporate_action_source_count: int = 0
    corporate_action_target_count: int = 0


def build_instrument_references(bundle: IngestionBundle) -> list[InstrumentReference]:
    observed: dict[str, _ObservedInstrument] = defaultdict(_ObservedInstrument)

    for item in bundle.transactions:
        facts = observed[item.instrument_code]
        facts.instrument_type_counts[item.instrument_type.value] += 1
        facts.asset_category_counts[_normalize_category(item.asset_category)] += 1
        facts.currency_counts[item.currency] += 1
        facts.transaction_count += 1

    for item in bundle.dividend_receipts:
        facts = observed[item.instrument_code]
        facts.instrument_type_counts[item.instrument_type.value] += 1
        facts.asset_category_counts[_normalize_category(item.asset_category)] += 1
        facts.currency_counts[item.currency] += 1
        facts.dividend_receipt_count += 1

    for item in bundle.corporate_actions:
        source_facts = observed[item.source_instrument_code]
        source_facts.instrument_type_counts[InstrumentType.UNKNOWN.value] += 1
        source_facts.corporate_action_source_count += 1

        target_facts = observed[item.target_instrument_code]
        target_facts.instrument_type_counts[InstrumentType.UNKNOWN.value] += 1
        target_facts.corporate_action_target_count += 1

    references: list[InstrumentReference] = []
    for canonical_code, facts in sorted(observed.items()):
        instrument_type, type_conflict = _resolve_instrument_type(facts.instrument_type_counts)
        asset_category, category_conflict = _resolve_text_value(
            facts.asset_category_counts,
            default=UNKNOWN_CATEGORY,
        )
        currency, currency_conflict = _resolve_text_value(
            facts.currency_counts,
            default="BRL",
        )
        notes = _build_notes(
            facts=facts,
            type_conflict=type_conflict,
            category_conflict=category_conflict,
            currency_conflict=currency_conflict,
        )
        identity_status = _build_identity_status(
            facts=facts,
            type_conflict=type_conflict,
            category_conflict=category_conflict,
            currency_conflict=currency_conflict,
        )
        references.append(
            InstrumentReference(
                canonical_code=canonical_code,
                instrument_type=InstrumentType(instrument_type),
                asset_category=asset_category,
                currency=currency,
                reference_origin=OBSERVED_REFERENCE_ORIGIN,
                identity_status=identity_status,
                first_batch_id=bundle.batch.batch_id,
                last_batch_id=bundle.batch.batch_id,
                notes=notes,
            )
        )
    return references


def _normalize_category(value: str) -> str:
    normalized = value.strip()
    return normalized if normalized else UNKNOWN_CATEGORY


def _resolve_instrument_type(counter: Counter[str]) -> tuple[str, bool]:
    known_values = Counter(
        {
            key: value
            for key, value in counter.items()
            if key and key != InstrumentType.UNKNOWN.value
        }
    )
    if not known_values:
        return InstrumentType.UNKNOWN.value, False
    if len(known_values) == 1:
        return next(iter(known_values)), False
    selected = sorted(
        known_values.items(),
        key=lambda item: (-item[1], item[0]),
    )[0][0]
    return selected, True


def _resolve_text_value(counter: Counter[str], *, default: str) -> tuple[str, bool]:
    known_values = Counter({key: value for key, value in counter.items() if key and key != default})
    if not known_values:
        return default, False
    if len(known_values) == 1:
        return next(iter(known_values)), False
    selected = sorted(
        known_values.items(),
        key=lambda item: (-item[1], item[0]),
    )[0][0]
    return selected, True


def _build_identity_status(
    *,
    facts: _ObservedInstrument,
    type_conflict: bool,
    category_conflict: bool,
    currency_conflict: bool,
) -> str:
    has_known_identity = any(
        key != InstrumentType.UNKNOWN.value and count > 0
        for key, count in facts.instrument_type_counts.items()
    )
    if not has_known_identity:
        return IDENTITY_STATUS_OBSERVED_ONLY
    if type_conflict or category_conflict or currency_conflict:
        return IDENTITY_STATUS_OBSERVED_CONFLICT
    return IDENTITY_STATUS_OBSERVED


def _build_notes(
    *,
    facts: _ObservedInstrument,
    type_conflict: bool,
    category_conflict: bool,
    currency_conflict: bool,
) -> str:
    notes: list[str] = []
    if facts.transaction_count == 0 and facts.dividend_receipt_count == 0:
        notes.append(
            "Reference created from corporate actions only; no trade or dividend facts observed."
        )
    if type_conflict:
        notes.append(f"Observed instrument types: {_format_counter(facts.instrument_type_counts)}.")
    if category_conflict:
        notes.append(f"Observed asset categories: {_format_counter(facts.asset_category_counts)}.")
    if currency_conflict:
        notes.append(f"Observed currencies: {_format_counter(facts.currency_counts)}.")
    if not notes:
        notes.append(
            "Reference normalized from canonical transaction, dividend, and corporate action facts."
        )
    return " ".join(notes)


def _format_counter(counter: Counter[str]) -> str:
    return ", ".join(
        f"{key}={value}"
        for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )
