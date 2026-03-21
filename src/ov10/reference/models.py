from __future__ import annotations

from dataclasses import dataclass

from ov10.domain.enums import InstrumentType


def _require_non_empty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


def _require_upper_code(value: str, field_name: str) -> str:
    return _require_non_empty(value, field_name).upper()


def _require_currency(value: str) -> str:
    normalized = _require_upper_code(value, "currency")
    if len(normalized) != 3:
        raise ValueError("currency must have length 3")
    return normalized


@dataclass(frozen=True, slots=True)
class InstrumentReference:
    canonical_code: str
    instrument_type: InstrumentType
    asset_category: str
    currency: str
    reference_origin: str
    identity_status: str
    first_batch_id: str
    last_batch_id: str
    notes: str | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_code",
            _require_upper_code(self.canonical_code, "canonical_code"),
        )
        object.__setattr__(
            self,
            "asset_category",
            _require_non_empty(self.asset_category, "asset_category"),
        )
        object.__setattr__(self, "currency", _require_currency(self.currency))
        object.__setattr__(
            self,
            "reference_origin",
            _require_non_empty(self.reference_origin, "reference_origin"),
        )
        object.__setattr__(
            self,
            "identity_status",
            _require_non_empty(self.identity_status, "identity_status"),
        )
        object.__setattr__(
            self,
            "first_batch_id",
            _require_non_empty(self.first_batch_id, "first_batch_id"),
        )
        object.__setattr__(
            self,
            "last_batch_id",
            _require_non_empty(self.last_batch_id, "last_batch_id"),
        )
