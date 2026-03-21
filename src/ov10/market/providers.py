from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Protocol
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from ov10.market.models import FxSnapshot, MarketProviderResult, MarketSnapshot

BRAPI_QUOTE_BASE_URL = "https://brapi.dev/api/quote"
BCB_PTAX_BASE_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
)


class JsonHttpClient(Protocol):
    def get_json(self, url: str, *, headers: dict[str, str] | None = None) -> dict[str, object]:
        """Fetch JSON payloads from an HTTP endpoint."""
        ...


class UrllibJsonHttpClient:
    def get_json(self, url: str, *, headers: dict[str, str] | None = None) -> dict[str, object]:
        request = Request(
            url,
            headers=headers or {"Accept": "application/json", "User-Agent": "ov10/0.1"},
        )
        with urlopen(request, timeout=30) as response:  # noqa: S310
            payload = json.load(response)
        if not isinstance(payload, dict):
            raise ValueError("HTTP client expected a JSON object response.")
        return {str(key): value for key, value in payload.items()}


class BrapiQuoteProvider:
    provider_name = "brapi"

    def __init__(
        self,
        *,
        http_client: JsonHttpClient | None = None,
        max_symbols_per_request: int = 4,
        token: str | None = None,
    ) -> None:
        self.http_client = http_client or UrllibJsonHttpClient()
        self.max_symbols_per_request = max_symbols_per_request
        self.token = token.strip() if token is not None and token.strip() else None

    def fetch_latest(
        self,
        canonical_codes: Sequence[str],
        *,
        as_of_date: date | None = None,
    ) -> MarketProviderResult:
        del as_of_date
        requested_codes = tuple(_normalize_code(item) for item in canonical_codes)
        snapshots: list[MarketSnapshot] = []
        unresolved_codes: set[str] = set()
        request_failed_codes: set[str] = set()

        for chunk in _chunked(requested_codes, size=self.max_symbols_per_request):
            if not chunk:
                continue
            try:
                payload = self.http_client.get_json(
                    self._build_quote_url(chunk),
                    headers=self._build_headers(),
                )
            except Exception:
                request_failed_codes.update(chunk)
                continue
            results = payload.get("results")
            if not isinstance(results, list):
                unresolved_codes.update(chunk)
                continue

            items_by_symbol = {
                _normalize_code(str(item.get("symbol", ""))): item
                for item in results
                if isinstance(item, dict) and item.get("symbol")
            }
            missing_in_chunk = set(chunk) - set(items_by_symbol)
            unresolved_codes.update(missing_in_chunk)

            for code in chunk:
                item = items_by_symbol.get(code)
                if item is None:
                    continue
                snapshot = _build_brapi_market_snapshot(item, provider_name=self.provider_name)
                if snapshot is None:
                    unresolved_codes.add(code)
                    continue
                snapshots.append(snapshot)

        return MarketProviderResult(
            snapshots=tuple(snapshots),
            unresolved_codes=tuple(sorted(unresolved_codes)),
            request_failed_codes=tuple(sorted(request_failed_codes)),
        )

    def _build_quote_url(self, symbols: Sequence[str]) -> str:
        joined_symbols = ",".join(symbols)
        params = urlencode({"range": "5d", "interval": "1d"})
        return f"{BRAPI_QUOTE_BASE_URL}/{quote(joined_symbols, safe=',')}?{params}"

    def _build_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "ov10/0.1"}
        if self.token is not None:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


class BCBPTAXProvider:
    provider_name = "bcb_ptax"

    def __init__(
        self,
        *,
        http_client: JsonHttpClient | None = None,
        lookback_days: int = 7,
    ) -> None:
        self.http_client = http_client or UrllibJsonHttpClient()
        self.lookback_days = lookback_days

    def fetch_latest(
        self,
        *,
        base_currency: str,
        quote_currency: str = "BRL",
        as_of_date: date | None = None,
    ) -> FxSnapshot:
        normalized_base = _normalize_code(base_currency)
        normalized_quote = _normalize_code(quote_currency)
        if normalized_quote != "BRL":
            raise ValueError("BCB PTAX provider currently supports quote_currency=BRL only")

        end_date = as_of_date or datetime.now(UTC).date()
        start_date = end_date - timedelta(days=self.lookback_days)
        payload = self.http_client.get_json(
            self._build_quote_url(
                base_currency=normalized_base,
                start_date=start_date,
                end_date=end_date,
            )
        )

        rows = payload.get("value")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"No PTAX data returned for {normalized_base}/{normalized_quote}")

        selected_row, observed_at = _select_bcb_row(rows)
        bid = Decimal(str(selected_row["cotacaoCompra"]))
        ask = Decimal(str(selected_row["cotacaoVenda"]))
        rate = (bid + ask) / Decimal("2")
        metadata = json.dumps(
            {
                "paridadeCompra": selected_row.get("paridadeCompra"),
                "paridadeVenda": selected_row.get("paridadeVenda"),
                "requested_start_date": start_date.isoformat(),
                "requested_end_date": end_date.isoformat(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return FxSnapshot(
            provider_name=self.provider_name,
            base_currency=normalized_base,
            quote_currency=normalized_quote,
            snapshot_date=observed_at.date(),
            observed_at=observed_at,
            retrieved_at=datetime.now(UTC),
            rate=rate,
            rate_kind="midpoint",
            bid=bid,
            ask=ask,
            bulletin_type=str(selected_row.get("tipoBoletim") or ""),
            provider_metadata_json=metadata,
        )

    def _build_quote_url(
        self,
        *,
        base_currency: str,
        start_date: date,
        end_date: date,
    ) -> str:
        params = urlencode(
            {
                "@moeda": f"'{base_currency}'",
                "@dataInicial": f"'{start_date.strftime('%m-%d-%Y')}'",
                "@dataFinalCotacao": f"'{end_date.strftime('%m-%d-%Y')}'",
                "$format": "json",
            }
        )
        return f"{BCB_PTAX_BASE_URL}?{params}"


def _build_brapi_market_snapshot(
    payload: dict[str, object],
    *,
    provider_name: str,
) -> MarketSnapshot | None:
    symbol = _normalize_code(str(payload.get("symbol", "")))
    price = payload.get("regularMarketPrice")
    if not symbol or price in {None, ""}:
        return None

    observed_at = _parse_brapi_time(payload.get("regularMarketTime"))
    historical = payload.get("historicalDataPrice")
    snapshot_date = _parse_brapi_snapshot_date(historical, fallback=observed_at.date())
    metadata = json.dumps(
        {
            "usedRange": payload.get("usedRange"),
            "usedInterval": payload.get("usedInterval"),
            "longName": payload.get("longName"),
            "currency": payload.get("currency"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return MarketSnapshot(
        canonical_code=symbol,
        provider_name=provider_name,
        source_symbol=symbol,
        snapshot_date=snapshot_date,
        observed_at=observed_at,
        retrieved_at=datetime.now(UTC),
        currency=str(payload.get("currency") or "BRL"),
        price=Decimal(str(price)),
        previous_close=_to_decimal_or_none(payload.get("regularMarketPreviousClose")),
        absolute_change=_to_decimal_or_none(payload.get("regularMarketChange")),
        percent_change=_to_decimal_or_none(payload.get("regularMarketChangePercent")),
        market="B3",
        quote_status="ok",
        provider_metadata_json=metadata,
    )


def _parse_brapi_time(value: object) -> datetime:
    if isinstance(value, str) and value:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    if isinstance(value, int | float):
        return datetime.fromtimestamp(float(value), UTC)
    return datetime.now(UTC)


def _parse_brapi_snapshot_date(value: object, *, fallback: date) -> date:
    if isinstance(value, list) and value:
        last = value[-1]
        if isinstance(last, dict):
            timestamp = last.get("date")
            if isinstance(timestamp, int | float):
                return datetime.fromtimestamp(float(timestamp), UTC).date()
    return fallback


def _select_bcb_row(rows: list[object]) -> tuple[dict[str, object], datetime]:
    parsed_rows: list[tuple[datetime, dict[str, object]]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        timestamp = row.get("dataHoraCotacao")
        if not isinstance(timestamp, str) or not timestamp.strip():
            continue
        observed_at = datetime.fromisoformat(timestamp.replace(" ", "T")).replace(tzinfo=UTC)
        parsed_rows.append((observed_at, row))

    if not parsed_rows:
        raise ValueError("No valid PTAX rows were returned by BCB")

    latest_date = max(item[0].date() for item in parsed_rows)
    candidates = [item for item in parsed_rows if item[0].date() == latest_date]
    closing_candidates = [
        item for item in candidates if str(item[1].get("tipoBoletim") or "").lower() == "fechamento"
    ]
    selected = max(closing_candidates or candidates, key=lambda item: item[0])
    return selected[1], selected[0]


def _chunked(items: Sequence[str], *, size: int) -> list[tuple[str, ...]]:
    return [tuple(items[index : index + size]) for index in range(0, len(items), size)]


def _normalize_code(value: str) -> str:
    return value.strip().upper()


def _to_decimal_or_none(value: object) -> Decimal | None:
    if value in {None, ""}:
        return None
    return Decimal(str(value))
