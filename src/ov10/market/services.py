from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from ov10.domain.enums import InstrumentType
from ov10.market.models import FxSnapshot
from ov10.market.providers import BCBPTAXProvider, BrapiQuoteProvider
from ov10.storage import SQLiteOV10Store, initialize_database

DEFAULT_FX_BASE_CURRENCIES = ("USD",)
BRAPI_SUPPORTED_TYPES = frozenset(
    {
        InstrumentType.STOCK_BR.value,
        InstrumentType.ETF_BR.value,
        InstrumentType.FII.value,
        InstrumentType.BDR.value,
    }
)


@dataclass(frozen=True, slots=True)
class SkippedSnapshotRequest:
    identifier: str
    reason: str
    message: str


@dataclass(frozen=True, slots=True)
class PublicMarketRefreshReport:
    database_path: str
    market_provider_name: str
    fx_provider_name: str
    base_currency: str
    market_snapshots_persisted: int
    fx_snapshots_persisted: int
    requested_instrument_codes: tuple[str, ...]
    selected_instrument_codes: tuple[str, ...]
    unresolved_market_codes: tuple[str, ...]
    fx_pairs: tuple[str, ...]
    skipped_requests: tuple[SkippedSnapshotRequest, ...]
    retrieved_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["retrieved_at"] = self.retrieved_at.isoformat()
        return payload


def refresh_public_market_data(
    database_path: str | Path,
    *,
    instrument_codes: list[str] | tuple[str, ...] | None = None,
    base_currency: str = "BRL",
    fx_base_currencies: list[str] | tuple[str, ...] | None = None,
    as_of_date: date | None = None,
    brapi_token: str | None = None,
    market_provider: BrapiQuoteProvider | None = None,
    fx_provider: BCBPTAXProvider | None = None,
) -> PublicMarketRefreshReport:
    normalized_base_currency = base_currency.strip().upper()
    requested_codes = tuple(sorted({_normalize_code(item) for item in instrument_codes or []}))
    requested_fx_bases = tuple(
        sorted(
            {
                _normalize_code(item)
                for item in (fx_base_currencies or DEFAULT_FX_BASE_CURRENCIES)
                if _normalize_code(item) != normalized_base_currency
            }
        )
    )

    market_provider = market_provider or BrapiQuoteProvider(token=brapi_token)
    fx_provider = fx_provider or BCBPTAXProvider()
    initialize_database(database_path)

    with SQLiteOV10Store(database_path) as store:
        store.initialize()
        references = store.list_active_instrument_references()

    skipped_requests: list[SkippedSnapshotRequest] = []
    references_by_code = {_normalize_code(str(item["canonical_code"])): item for item in references}
    candidate_codes = requested_codes or tuple(sorted(references_by_code))
    selected_codes: list[str] = []
    for code in candidate_codes:
        reference = references_by_code.get(code)
        if reference is None:
            skipped_requests.append(
                SkippedSnapshotRequest(
                    identifier=code,
                    reason="instrument_reference_missing",
                    message="No active instrument reference exists for this canonical code.",
                )
            )
            continue

        instrument_type = str(reference["instrument_type"])
        currency = str(reference["currency"])
        if instrument_type not in BRAPI_SUPPORTED_TYPES:
            skipped_requests.append(
                SkippedSnapshotRequest(
                    identifier=code,
                    reason="unsupported_instrument_type",
                    message=(
                        f"Instrument type `{instrument_type}` is not yet supported by the "
                        "governed brapi adapter."
                    ),
                )
            )
            continue
        if currency != normalized_base_currency:
            skipped_requests.append(
                SkippedSnapshotRequest(
                    identifier=code,
                    reason="unsupported_instrument_currency",
                    message=(
                        f"Instrument currency `{currency}` does not match base currency "
                        f"`{normalized_base_currency}` for the first market adapter pass."
                    ),
                )
            )
            continue

        selected_codes.append(code)

    market_result = market_provider.fetch_latest(selected_codes, as_of_date=as_of_date)
    if market_result.unresolved_codes:
        skipped_requests.extend(
            SkippedSnapshotRequest(
                identifier=code,
                reason="provider_unresolved",
                message=(
                    "The public market provider did not return a usable quote for this instrument."
                ),
            )
            for code in market_result.unresolved_codes
        )
    if market_result.request_failed_codes:
        skipped_requests.extend(
            SkippedSnapshotRequest(
                identifier=code,
                reason="provider_request_failed",
                message=(
                    "The public market provider request failed before a quote could be classified."
                ),
            )
            for code in market_result.request_failed_codes
        )

    fx_snapshots: list[FxSnapshot] = []
    for fx_base in requested_fx_bases:
        try:
            fx_snapshots.append(
                fx_provider.fetch_latest(
                    base_currency=fx_base,
                    quote_currency=normalized_base_currency,
                    as_of_date=as_of_date,
                )
            )
        except Exception as exc:
            skipped_requests.append(
                SkippedSnapshotRequest(
                    identifier=f"{fx_base}/{normalized_base_currency}",
                    reason="fx_provider_failed",
                    message=f"FX provider failed: {exc}",
                )
            )

    with SQLiteOV10Store(database_path) as store:
        store.initialize()
        market_snapshots_persisted = store.upsert_market_snapshots(list(market_result.snapshots))
        fx_snapshots_persisted = store.upsert_fx_snapshots(fx_snapshots)

    return PublicMarketRefreshReport(
        database_path=str(Path(database_path).resolve()),
        market_provider_name=market_provider.provider_name,
        fx_provider_name=fx_provider.provider_name,
        base_currency=normalized_base_currency,
        market_snapshots_persisted=market_snapshots_persisted,
        fx_snapshots_persisted=fx_snapshots_persisted,
        requested_instrument_codes=candidate_codes,
        selected_instrument_codes=tuple(sorted(selected_codes)),
        unresolved_market_codes=market_result.unresolved_codes,
        fx_pairs=tuple(f"{item.base_currency}/{item.quote_currency}" for item in fx_snapshots),
        skipped_requests=tuple(
            sorted(skipped_requests, key=lambda item: (item.reason, item.identifier))
        ),
        retrieved_at=datetime.now(UTC),
    )


def _normalize_code(value: str) -> str:
    return value.strip().upper()
