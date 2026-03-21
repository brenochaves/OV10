from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from ov10.cli import main
from ov10.domain import ImportBatch, IngestionBundle, InstrumentType, SourceSystem
from ov10.market import FxSnapshot, MarketProviderResult, MarketSnapshot, refresh_public_market_data
from ov10.market.providers import BCBPTAXProvider, BrapiQuoteProvider
from ov10.reference import InstrumentReference
from ov10.storage import SQLiteOV10Store, initialize_database


class _StubJsonHttpClient:
    def __init__(self, *responses: dict[str, object]) -> None:
        self.responses = list(responses)
        self.urls: list[str] = []
        self.headers: list[dict[str, str] | None] = []

    def get_json(self, url: str, *, headers: dict[str, str] | None = None) -> dict[str, object]:
        self.urls.append(url)
        self.headers.append(headers)
        return self.responses.pop(0)


class _StaticMarketProvider:
    provider_name = "stub_market"

    def __init__(
        self,
        *,
        snapshots: tuple[MarketSnapshot, ...],
        unresolved_codes: tuple[str, ...] = (),
    ) -> None:
        self.snapshots = snapshots
        self.unresolved_codes = unresolved_codes
        self.calls: list[tuple[tuple[str, ...], date | None]] = []

    def fetch_latest(
        self,
        canonical_codes: tuple[str, ...] | list[str],
        *,
        as_of_date: date | None = None,
    ) -> MarketProviderResult:
        requested = tuple(canonical_codes)
        self.calls.append((requested, as_of_date))
        return MarketProviderResult(
            snapshots=tuple(
                item for item in self.snapshots if item.canonical_code in set(requested)
            ),
            unresolved_codes=tuple(
                code for code in self.unresolved_codes if code in set(requested)
            ),
        )


class _StaticFxProvider:
    provider_name = "stub_fx"

    def __init__(self, *, snapshot: FxSnapshot) -> None:
        self.snapshot = snapshot
        self.calls: list[tuple[str, str, date | None]] = []

    def fetch_latest(
        self,
        *,
        base_currency: str,
        quote_currency: str = "BRL",
        as_of_date: date | None = None,
    ) -> FxSnapshot:
        self.calls.append((base_currency, quote_currency, as_of_date))
        return self.snapshot


class MarketProviderTests(unittest.TestCase):
    def test_market_snapshot_rejects_invalid_metadata_json(self) -> None:
        with self.assertRaisesRegex(ValueError, "provider_metadata_json must contain valid JSON"):
            MarketSnapshot(
                canonical_code="PETR4",
                provider_name="stub_market",
                source_symbol="PETR4",
                snapshot_date=date(2026, 3, 20),
                observed_at=datetime(2026, 3, 21, 12, 0, tzinfo=UTC),
                retrieved_at=datetime(2026, 3, 21, 12, 1, tzinfo=UTC),
                currency="BRL",
                price=Decimal("45.67"),
                provider_metadata_json="{invalid",
            )

    def test_brapi_provider_parses_quote_payload(self) -> None:
        http_client = _StubJsonHttpClient(
            {
                "requestedAt": "2026-03-21T12:00:00Z",
                "results": [
                    {
                        "symbol": "PETR4",
                        "currency": "BRL",
                        "regularMarketTime": "2026-03-21T09:42:02.000Z",
                        "regularMarketPrice": 45.67,
                        "regularMarketPreviousClose": 46.78,
                        "regularMarketChange": -1.11,
                        "regularMarketChangePercent": -2.37,
                        "usedRange": "5d",
                        "usedInterval": "1d",
                        "longName": "Petroleo Brasileiro",
                        "historicalDataPrice": [
                            {
                                "date": 1773975600,
                                "close": 45.67,
                                "adjustedClose": 45.67,
                            }
                        ],
                    }
                ],
            }
        )
        provider = BrapiQuoteProvider(http_client=http_client)

        result = provider.fetch_latest(["PETR4"])

        self.assertEqual(len(result.snapshots), 1)
        self.assertFalse(result.unresolved_codes)
        snapshot = result.snapshots[0]
        self.assertEqual(snapshot.canonical_code, "PETR4")
        self.assertEqual(snapshot.snapshot_date, date(2026, 3, 20))
        self.assertEqual(snapshot.currency, "BRL")
        self.assertEqual(snapshot.price, Decimal("45.67"))
        self.assertEqual(snapshot.previous_close, Decimal("46.78"))
        self.assertEqual(snapshot.absolute_change, Decimal("-1.11"))
        self.assertEqual(snapshot.percent_change, Decimal("-2.37"))
        self.assertEqual(snapshot.market, "B3")
        self.assertIn("/PETR4?range=5d&interval=1d", http_client.urls[0])

    def test_brapi_provider_includes_bearer_token_when_configured(self) -> None:
        http_client = _StubJsonHttpClient({"results": []})
        provider = BrapiQuoteProvider(http_client=http_client, token="secret-token")

        provider.fetch_latest(["PETR4"])

        self.assertEqual(http_client.headers[0]["Authorization"], "Bearer secret-token")

    def test_bcb_provider_uses_latest_closing_quote_and_midpoint_rate(self) -> None:
        http_client = _StubJsonHttpClient(
            {
                "value": [
                    {
                        "cotacaoCompra": 5.2097,
                        "cotacaoVenda": 5.2103,
                        "dataHoraCotacao": "2026-03-20 10:11:27.571",
                        "tipoBoletim": "Abertura",
                        "paridadeCompra": 1.0,
                        "paridadeVenda": 1.0,
                    },
                    {
                        "cotacaoCompra": 5.2793,
                        "cotacaoVenda": 5.28,
                        "dataHoraCotacao": "2026-03-20 13:11:27.571",
                        "tipoBoletim": "Fechamento",
                        "paridadeCompra": 1.0,
                        "paridadeVenda": 1.0,
                    },
                ]
            }
        )
        provider = BCBPTAXProvider(http_client=http_client, lookback_days=3)

        snapshot = provider.fetch_latest(
            base_currency="USD",
            quote_currency="BRL",
            as_of_date=date(2026, 3, 21),
        )

        self.assertEqual(snapshot.base_currency, "USD")
        self.assertEqual(snapshot.quote_currency, "BRL")
        self.assertEqual(snapshot.snapshot_date, date(2026, 3, 20))
        self.assertEqual(snapshot.bid, Decimal("5.2793"))
        self.assertEqual(snapshot.ask, Decimal("5.28"))
        self.assertEqual(snapshot.rate, Decimal("5.27965"))
        self.assertEqual(snapshot.rate_kind, "midpoint")
        self.assertEqual(snapshot.bulletin_type, "Fechamento")
        self.assertIn("%40moeda=%27USD%27", http_client.urls[0])


class MarketRefreshServiceTests(unittest.TestCase):
    def test_refresh_public_market_data_persists_snapshots_and_cli_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "ov10.sqlite3"
            self._seed_reference_database(database_path)

            market_provider = _StaticMarketProvider(
                snapshots=(
                    MarketSnapshot(
                        canonical_code="PETR4",
                        provider_name="stub_market",
                        source_symbol="PETR4",
                        snapshot_date=date(2026, 3, 20),
                        observed_at=datetime(2026, 3, 21, 12, 0, tzinfo=UTC),
                        retrieved_at=datetime(2026, 3, 21, 12, 1, tzinfo=UTC),
                        currency="BRL",
                        price=Decimal("45.67"),
                        previous_close=Decimal("46.78"),
                        absolute_change=Decimal("-1.11"),
                        percent_change=Decimal("-2.37"),
                        market="B3",
                        provider_metadata_json=json.dumps({"source": "test"}, sort_keys=True),
                    ),
                )
            )
            fx_provider = _StaticFxProvider(
                snapshot=FxSnapshot(
                    provider_name="stub_fx",
                    base_currency="USD",
                    quote_currency="BRL",
                    snapshot_date=date(2026, 3, 20),
                    observed_at=datetime(2026, 3, 20, 13, 11, tzinfo=UTC),
                    retrieved_at=datetime(2026, 3, 21, 12, 1, tzinfo=UTC),
                    rate=Decimal("5.27965"),
                    rate_kind="midpoint",
                    bid=Decimal("5.2793"),
                    ask=Decimal("5.28"),
                    bulletin_type="Fechamento",
                    provider_metadata_json=json.dumps({"source": "test"}, sort_keys=True),
                )
            )

            report = refresh_public_market_data(
                database_path,
                instrument_codes=["PETR4", "AAPL", "MISSING1"],
                fx_base_currencies=["USD"],
                as_of_date=date(2026, 3, 21),
                market_provider=market_provider,
                fx_provider=fx_provider,
            )

            self.assertEqual(report.market_snapshots_persisted, 1)
            self.assertEqual(report.fx_snapshots_persisted, 1)
            self.assertEqual(report.selected_instrument_codes, ("PETR4",))
            self.assertEqual(report.fx_pairs, ("USD/BRL",))
            self.assertEqual(market_provider.calls, [(("PETR4",), date(2026, 3, 21))])
            self.assertEqual(fx_provider.calls, [("USD", "BRL", date(2026, 3, 21))])
            self.assertEqual(
                {(item.identifier, item.reason) for item in report.skipped_requests},
                {
                    ("AAPL", "unsupported_instrument_type"),
                    ("MISSING1", "instrument_reference_missing"),
                },
            )

            with SQLiteOV10Store(database_path) as store:
                store.initialize()
                self.assertEqual(store.count_rows("market_snapshot"), 1)
                self.assertEqual(store.count_rows("fx_snapshot"), 1)
                market_report = store.fetch_market_snapshot_report(canonical_code="PETR4")
                fx_report = store.fetch_fx_snapshot_report(
                    base_currency="USD",
                    quote_currency="BRL",
                )

            self.assertEqual(market_report["counts"]["snapshots"], 1)
            self.assertEqual(market_report["latest_snapshots"][0]["price"], "45.67")
            self.assertEqual(
                market_report["latest_snapshots"][0]["provider_metadata"]["source"],
                "test",
            )
            self.assertEqual(fx_report["counts"]["snapshots"], 1)
            self.assertEqual(fx_report["latest_snapshots"][0]["rate"], "5.27965")
            self.assertEqual(
                fx_report["latest_snapshots"][0]["provider_metadata"]["source"],
                "test",
            )

            market_stdout = io.StringIO()
            with redirect_stdout(market_stdout):
                exit_code = main(
                    [
                        "market-snapshot-report",
                        "--database",
                        str(database_path),
                        "--canonical-code",
                        "PETR4",
                    ]
                )
            self.assertEqual(exit_code, 0)
            market_cli_payload = json.loads(market_stdout.getvalue())
            self.assertEqual(market_cli_payload["counts"]["snapshots"], 1)
            self.assertEqual(market_cli_payload["latest_snapshots"][0]["canonical_code"], "PETR4")

            fx_stdout = io.StringIO()
            with redirect_stdout(fx_stdout):
                exit_code = main(
                    [
                        "fx-snapshot-report",
                        "--database",
                        str(database_path),
                        "--base-currency",
                        "USD",
                        "--quote-currency",
                        "BRL",
                    ]
                )
            self.assertEqual(exit_code, 0)
            fx_cli_payload = json.loads(fx_stdout.getvalue())
            self.assertEqual(fx_cli_payload["counts"]["snapshots"], 1)
            self.assertEqual(fx_cli_payload["latest_snapshots"][0]["base_currency"], "USD")

    def _seed_reference_database(self, database_path: Path) -> None:
        initialize_database(database_path)
        batch = ImportBatch(
            batch_id="seed:market",
            source_system=SourceSystem.STATUS_INVEST_XLSX,
            source_file="seed.xlsx",
            file_sha256="seed-hash",
            imported_at=datetime(2026, 3, 21, 12, 0, tzinfo=UTC),
        )
        bundle = IngestionBundle(
            batch=batch,
            transactions=(),
            dividend_receipts=(),
            corporate_actions=(),
        )
        references = [
            InstrumentReference(
                canonical_code="PETR4",
                instrument_type=InstrumentType.STOCK_BR,
                asset_category="Ações",
                currency="BRL",
                reference_origin="seed",
                identity_status="observed_identity",
                first_batch_id=batch.batch_id,
                last_batch_id=batch.batch_id,
            ),
            InstrumentReference(
                canonical_code="AAPL",
                instrument_type=InstrumentType.STOCK_US,
                asset_category="Stocks",
                currency="USD",
                reference_origin="seed",
                identity_status="observed_identity",
                first_batch_id=batch.batch_id,
                last_batch_id=batch.batch_id,
            ),
        ]
        with SQLiteOV10Store(database_path) as store:
            store.initialize()
            store.persist_ingestion_bundle(bundle)
            store.upsert_instrument_references(references)
