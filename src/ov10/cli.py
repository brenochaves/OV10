from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

from ov10.ingestion import load_status_invest_workbook
from ov10.market import DEFAULT_FX_BASE_CURRENCIES, refresh_public_market_data
from ov10.positions import POSITION_ENGINE_VERSION, compute_positions
from ov10.reconciliation import (
    DEFAULT_REFERENCE_WORKBOOK_PATH,
    generate_reference_workbook_reconciliation,
)
from ov10.research import (
    DEFAULT_BRIDGE_KEY,
    DEFAULT_BRIDGE_URL,
    DEFAULT_REFERENCE_SPREADSHEET_ID,
    RuntimeBridgeClient,
    analyze_remote_script_artifact,
    capture_remote_script_artifact,
    create_debug_copy,
)
from ov10.services import persist_status_invest_xlsx
from ov10.storage import SQLiteOV10Store, initialize_database
from ov10.testing import (
    build_synthetic_status_invest_workbook,
    generate_synthetic_status_invest_matrix,
    list_synthetic_status_invest_scenarios,
)

DEFAULT_DATABASE_PATH = Path("var/ov10.sqlite3")
DEFAULT_CONFIG_PATH = Path("config/ov10_portfolio.toml")
DEFAULT_SOURCE_WORKBOOK_PATH = Path("data/OV10_base_2025.xlsx")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ov10")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest-status-invest-xlsx")
    ingest_parser.add_argument("path", type=Path)

    positions_parser = subparsers.add_parser("positions-from-xlsx")
    positions_parser.add_argument("path", type=Path)

    init_db_parser = subparsers.add_parser("init-db")
    init_db_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )

    persist_parser = subparsers.add_parser("persist-status-invest-xlsx")
    persist_parser.add_argument("path", type=Path)
    persist_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )
    persist_parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
    )

    batch_report_parser = subparsers.add_parser("batch-report")
    batch_report_parser.add_argument("batch_id")
    batch_report_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )

    instrument_reference_parser = subparsers.add_parser("instrument-reference-report")
    instrument_reference_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )
    instrument_reference_parser.add_argument(
        "--batch-id",
        default=None,
    )

    refresh_market_parser = subparsers.add_parser("refresh-public-market-data")
    refresh_market_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )
    refresh_market_parser.add_argument(
        "--instrument-code",
        dest="instrument_codes",
        action="append",
        default=None,
    )
    refresh_market_parser.add_argument(
        "--base-currency",
        default="BRL",
    )
    refresh_market_parser.add_argument(
        "--fx-base-currency",
        dest="fx_base_currencies",
        action="append",
        default=list(DEFAULT_FX_BASE_CURRENCIES),
    )
    refresh_market_parser.add_argument(
        "--as-of-date",
        type=date.fromisoformat,
        default=None,
    )
    refresh_market_parser.add_argument(
        "--brapi-token",
        default=os.getenv("OV10_BRAPI_TOKEN"),
    )

    market_snapshot_parser = subparsers.add_parser("market-snapshot-report")
    market_snapshot_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )
    market_snapshot_parser.add_argument(
        "--canonical-code",
        default=None,
    )
    market_snapshot_parser.add_argument(
        "--provider",
        default=None,
    )

    fx_snapshot_parser = subparsers.add_parser("fx-snapshot-report")
    fx_snapshot_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )
    fx_snapshot_parser.add_argument(
        "--base-currency",
        default=None,
    )
    fx_snapshot_parser.add_argument(
        "--quote-currency",
        default=None,
    )
    fx_snapshot_parser.add_argument(
        "--provider",
        default=None,
    )

    list_batches_parser = subparsers.add_parser("list-batches")
    list_batches_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )

    cash_balances_parser = subparsers.add_parser("cash-balances")
    cash_balances_parser.add_argument("batch_id")
    cash_balances_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )

    book_positions_parser = subparsers.add_parser("book-positions")
    book_positions_parser.add_argument("batch_id")
    book_positions_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )

    synthetic_parser = subparsers.add_parser("generate-synthetic-status-invest-xlsx")
    synthetic_parser.add_argument("path", type=Path)
    synthetic_parser.add_argument(
        "--scenario",
        required=True,
        choices=list_synthetic_status_invest_scenarios(),
    )

    synthetic_matrix_parser = subparsers.add_parser("generate-synthetic-status-invest-matrix")
    synthetic_matrix_parser.add_argument("output_dir", type=Path)

    create_debug_copy_parser = subparsers.add_parser("create-online-debug-copy")
    create_debug_copy_parser.add_argument(
        "--bridge-url",
        default=DEFAULT_BRIDGE_URL,
    )
    create_debug_copy_parser.add_argument(
        "--bridge-key",
        default=DEFAULT_BRIDGE_KEY,
    )
    create_debug_copy_parser.add_argument(
        "--spreadsheet-id",
        default=DEFAULT_REFERENCE_SPREADSHEET_ID,
    )
    create_debug_copy_parser.add_argument(
        "--copy-name-prefix",
        default="OV10 Debug Copy",
    )

    capture_remote_script_parser = subparsers.add_parser("capture-online-remote-script")
    capture_remote_script_parser.add_argument(
        "output_dir",
        type=Path,
    )
    capture_remote_script_parser.add_argument(
        "--bridge-url",
        default=DEFAULT_BRIDGE_URL,
    )
    capture_remote_script_parser.add_argument(
        "--bridge-key",
        default=DEFAULT_BRIDGE_KEY,
    )
    capture_remote_script_parser.add_argument(
        "--spreadsheet-id",
        default=DEFAULT_REFERENCE_SPREADSHEET_ID,
    )
    capture_remote_script_parser.add_argument(
        "--chunk-length",
        type=int,
        default=50_000,
    )

    analyze_remote_script_parser = subparsers.add_parser("analyze-online-remote-script")
    analyze_remote_script_parser.add_argument(
        "payload_path",
        type=Path,
    )
    analyze_remote_script_parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
    )

    reference_reconciliation_parser = subparsers.add_parser("reference-workbook-reconciliation")
    reference_reconciliation_parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=DEFAULT_SOURCE_WORKBOOK_PATH,
    )
    reference_reconciliation_parser.add_argument(
        "--reference-workbook",
        type=Path,
        default=DEFAULT_REFERENCE_WORKBOOK_PATH,
    )
    reference_reconciliation_parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
    )
    reference_reconciliation_parser.add_argument(
        "--database",
        type=Path,
        default=None,
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "ingest-status-invest-xlsx":
        bundle = load_status_invest_workbook(args.path)
        print(json.dumps(bundle.summary(), indent=2))
        return 0

    if args.command == "positions-from-xlsx":
        bundle = load_status_invest_workbook(args.path)
        snapshots = compute_positions(bundle.transactions)
        payload = [asdict(snapshot) for snapshot in snapshots]
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "init-db":
        database_path = initialize_database(args.database)
        print(json.dumps({"database_path": str(database_path.resolve())}, indent=2))
        return 0

    if args.command == "persist-status-invest-xlsx":
        report = persist_status_invest_xlsx(
            args.path,
            database_path=args.database,
            config_path=args.config,
        )
        print(json.dumps(report.to_dict(), indent=2, default=_json_default))
        return 0

    if args.command == "batch-report":
        with SQLiteOV10Store(args.database) as store:
            store.initialize()
            report = store.fetch_batch_report(
                batch_id=args.batch_id,
                engine_version=POSITION_ENGINE_VERSION,
            )
        if report is None:
            parser.error(f"Unknown batch_id: {args.batch_id}")
        print(json.dumps(report, indent=2, default=_json_default))
        return 0

    if args.command == "instrument-reference-report":
        with SQLiteOV10Store(args.database) as store:
            store.initialize()
            payload = store.fetch_instrument_reference_report(batch_id=args.batch_id)
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "refresh-public-market-data":
        payload = refresh_public_market_data(
            args.database,
            instrument_codes=args.instrument_codes,
            base_currency=args.base_currency,
            fx_base_currencies=args.fx_base_currencies,
            as_of_date=args.as_of_date,
            brapi_token=args.brapi_token,
        )
        print(json.dumps(payload.to_dict(), indent=2, default=_json_default))
        return 0

    if args.command == "market-snapshot-report":
        with SQLiteOV10Store(args.database) as store:
            store.initialize()
            payload = store.fetch_market_snapshot_report(
                canonical_code=args.canonical_code,
                provider_name=args.provider,
            )
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "fx-snapshot-report":
        with SQLiteOV10Store(args.database) as store:
            store.initialize()
            payload = store.fetch_fx_snapshot_report(
                base_currency=args.base_currency,
                quote_currency=args.quote_currency,
                provider_name=args.provider,
            )
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "list-batches":
        with SQLiteOV10Store(args.database) as store:
            store.initialize()
            payload = store.list_batches(engine_version=POSITION_ENGINE_VERSION)
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "cash-balances":
        with SQLiteOV10Store(args.database) as store:
            store.initialize()
            report = store.fetch_batch_report(
                batch_id=args.batch_id,
                engine_version=POSITION_ENGINE_VERSION,
            )
        if report is None:
            parser.error(f"Unknown batch_id: {args.batch_id}")
        accounts = _require_payload_mapping_list(report, "accounts")
        cash_balance_snapshots = _require_payload_mapping_list(report, "cash_balance_snapshots")
        accounts_by_id = {
            _require_payload_string(item, "account_id", context="accounts"): item
            for item in accounts
        }
        payload = []
        for item in cash_balance_snapshots:
            account_id = _require_payload_string(
                item, "account_id", context="cash_balance_snapshots"
            )
            account = accounts_by_id.get(account_id, {})
            payload.append(
                {
                    "account_id": account_id,
                    "account_name": account.get("account_name"),
                    "account_type": account.get("account_type"),
                    "snapshot_date": item["snapshot_date"],
                    "currency": item["currency"],
                    "balance": item["balance"],
                }
            )
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "book-positions":
        with SQLiteOV10Store(args.database) as store:
            store.initialize()
            report = store.fetch_batch_report(
                batch_id=args.batch_id,
                engine_version=POSITION_ENGINE_VERSION,
            )
        if report is None:
            parser.error(f"Unknown batch_id: {args.batch_id}")
        print(json.dumps(report["book_position_snapshots"], indent=2, default=_json_default))
        return 0

    if args.command == "generate-synthetic-status-invest-xlsx":
        payload = build_synthetic_status_invest_workbook(
            args.path,
            scenario_name=args.scenario,
        )
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "generate-synthetic-status-invest-matrix":
        payload = generate_synthetic_status_invest_matrix(args.output_dir)
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "create-online-debug-copy":
        client = RuntimeBridgeClient(
            bridge_url=args.bridge_url,
            bridge_key=args.bridge_key,
            spreadsheet_id=args.spreadsheet_id,
        )
        payload = create_debug_copy(
            client,
            copy_name_prefix=args.copy_name_prefix,
        )
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "capture-online-remote-script":
        client = RuntimeBridgeClient(
            bridge_url=args.bridge_url,
            bridge_key=args.bridge_key,
            spreadsheet_id=args.spreadsheet_id,
        )
        payload = capture_remote_script_artifact(
            args.output_dir,
            client=client,
            chunk_length=args.chunk_length,
        )
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "analyze-online-remote-script":
        payload = analyze_remote_script_artifact(
            args.payload_path,
            output_path=args.output_path,
        )
        print(json.dumps(payload, indent=2, default=_json_default))
        return 0

    if args.command == "reference-workbook-reconciliation":
        payload = generate_reference_workbook_reconciliation(
            args.path,
            reference_workbook_path=args.reference_workbook,
            config_path=args.config,
            database_path=args.database,
        )
        print(json.dumps(payload.to_dict(), indent=2, default=_json_default))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def _json_default(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date | datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _require_payload_mapping_list(
    payload: dict[str, object],
    key: str,
) -> list[dict[str, object]]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Expected `{key}` to be a list.")
    items: list[dict[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"Expected `{key}[{index}]` to be an object.")
        items.append({str(field): cast_value for field, cast_value in item.items()})
    return items


def _require_payload_string(item: dict[str, object], key: str, *, context: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Expected `{context}.{key}` to be a non-empty string.")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
