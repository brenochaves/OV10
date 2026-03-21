CREATE TABLE IF NOT EXISTS import_batch (
    batch_id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_file TEXT NOT NULL,
    file_sha256 TEXT NOT NULL UNIQUE,
    imported_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_record (
    source_record_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    source_system TEXT NOT NULL,
    source_file TEXT NOT NULL,
    sheet_name TEXT NOT NULL,
    row_number INTEGER NOT NULL,
    source_row_ref TEXT NOT NULL,
    UNIQUE (batch_id, sheet_name, row_number)
);

CREATE TABLE IF NOT EXISTS canonical_transaction (
    transaction_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    source_record_id TEXT NOT NULL REFERENCES source_record (source_record_id) ON DELETE CASCADE,
    trade_date TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    instrument_code TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    asset_category TEXT NOT NULL,
    broker_name TEXT NOT NULL,
    quantity TEXT NOT NULL,
    unit_price TEXT NOT NULL,
    gross_amount TEXT NOT NULL,
    fees TEXT NOT NULL,
    cash_effect TEXT NOT NULL,
    cost_basis_effect TEXT,
    currency TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_canonical_transaction_batch
ON canonical_transaction (batch_id, instrument_code, trade_date);

CREATE TABLE IF NOT EXISTS canonical_dividend_receipt (
    receipt_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    source_record_id TEXT NOT NULL REFERENCES source_record (source_record_id) ON DELETE CASCADE,
    reference_date TEXT,
    received_date TEXT NOT NULL,
    instrument_code TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    asset_category TEXT NOT NULL,
    broker_name TEXT NOT NULL,
    dividend_type TEXT NOT NULL,
    payable_quantity TEXT NOT NULL,
    gross_amount TEXT NOT NULL,
    withholding_tax TEXT NOT NULL,
    net_amount TEXT NOT NULL,
    currency TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_canonical_dividend_receipt_batch
ON canonical_dividend_receipt (batch_id, instrument_code, received_date);

CREATE TABLE IF NOT EXISTS canonical_corporate_action (
    corporate_action_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    source_record_id TEXT NOT NULL REFERENCES source_record (source_record_id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    source_instrument_code TEXT NOT NULL,
    target_instrument_code TEXT NOT NULL,
    quantity_from TEXT NOT NULL,
    quantity_to TEXT NOT NULL,
    cost_basis_transferred TEXT NOT NULL,
    cash_component TEXT NOT NULL,
    comments TEXT
);

CREATE INDEX IF NOT EXISTS ix_canonical_corporate_action_batch
ON canonical_corporate_action (batch_id, effective_date);

CREATE TABLE IF NOT EXISTS instrument_mapping (
    mapping_id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_code TEXT NOT NULL,
    canonical_code TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    mapping_origin TEXT NOT NULL,
    first_batch_id TEXT NOT NULL REFERENCES import_batch (batch_id),
    last_batch_id TEXT NOT NULL REFERENCES import_batch (batch_id),
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (source_system, source_code)
);

CREATE TABLE IF NOT EXISTS instrument_reference (
    canonical_code TEXT PRIMARY KEY,
    instrument_type TEXT NOT NULL,
    asset_category TEXT NOT NULL,
    currency TEXT NOT NULL,
    reference_origin TEXT NOT NULL,
    identity_status TEXT NOT NULL,
    first_batch_id TEXT NOT NULL REFERENCES import_batch (batch_id),
    last_batch_id TEXT NOT NULL REFERENCES import_batch (batch_id),
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS market_snapshot (
    provider_name TEXT NOT NULL,
    canonical_code TEXT NOT NULL REFERENCES instrument_reference (canonical_code),
    source_symbol TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    currency TEXT NOT NULL,
    price TEXT NOT NULL,
    previous_close TEXT,
    absolute_change TEXT,
    percent_change TEXT,
    market TEXT,
    quote_status TEXT NOT NULL,
    provider_metadata_json TEXT,
    PRIMARY KEY (provider_name, canonical_code, snapshot_date)
);

CREATE INDEX IF NOT EXISTS ix_market_snapshot_latest
ON market_snapshot (canonical_code, snapshot_date DESC, provider_name);

CREATE TABLE IF NOT EXISTS fx_snapshot (
    provider_name TEXT NOT NULL,
    base_currency TEXT NOT NULL,
    quote_currency TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    rate TEXT NOT NULL,
    rate_kind TEXT NOT NULL,
    bid TEXT,
    ask TEXT,
    bulletin_type TEXT,
    provider_metadata_json TEXT,
    PRIMARY KEY (provider_name, base_currency, quote_currency, snapshot_date)
);

CREATE INDEX IF NOT EXISTS ix_fx_snapshot_latest
ON fx_snapshot (base_currency, quote_currency, snapshot_date DESC, provider_name);

CREATE TABLE IF NOT EXISTS account_registry (
    account_id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    account_type TEXT NOT NULL,
    account_name TEXT NOT NULL,
    first_batch_id TEXT NOT NULL REFERENCES import_batch (batch_id),
    last_batch_id TEXT NOT NULL REFERENCES import_batch (batch_id),
    currency TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS portfolio_registry (
    portfolio_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    profile TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS book_registry (
    book_id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL REFERENCES portfolio_registry (portfolio_id),
    name TEXT NOT NULL,
    target_weight TEXT NOT NULL,
    instrument_types_json TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS account_portfolio_assignment (
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    account_id TEXT NOT NULL REFERENCES account_registry (account_id),
    portfolio_id TEXT NOT NULL REFERENCES portfolio_registry (portfolio_id),
    PRIMARY KEY (batch_id, account_id)
);

CREATE TABLE IF NOT EXISTS cash_movement (
    movement_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    account_id TEXT NOT NULL REFERENCES account_registry (account_id),
    movement_date TEXT NOT NULL,
    movement_type TEXT NOT NULL,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    related_record_type TEXT NOT NULL,
    related_record_id TEXT NOT NULL,
    instrument_code TEXT,
    description TEXT
);

CREATE INDEX IF NOT EXISTS ix_cash_movement_batch
ON cash_movement (batch_id, account_id, movement_date);

CREATE TABLE IF NOT EXISTS cash_balance_snapshot (
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    snapshot_date TEXT NOT NULL,
    account_id TEXT NOT NULL REFERENCES account_registry (account_id),
    currency TEXT NOT NULL,
    balance TEXT NOT NULL,
    PRIMARY KEY (batch_id, account_id, currency)
);

CREATE TABLE IF NOT EXISTS account_position_snapshot (
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    snapshot_date TEXT NOT NULL,
    account_id TEXT NOT NULL REFERENCES account_registry (account_id),
    instrument_code TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    quantity TEXT NOT NULL,
    total_cost TEXT NOT NULL,
    avg_cost TEXT NOT NULL,
    currency TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    PRIMARY KEY (batch_id, account_id, instrument_code, engine_version)
);

CREATE INDEX IF NOT EXISTS ix_account_position_snapshot_batch
ON account_position_snapshot (batch_id, engine_version, account_id);

CREATE TABLE IF NOT EXISTS book_position_snapshot (
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    snapshot_date TEXT NOT NULL,
    portfolio_id TEXT NOT NULL REFERENCES portfolio_registry (portfolio_id),
    book_id TEXT NOT NULL REFERENCES book_registry (book_id),
    account_id TEXT NOT NULL REFERENCES account_registry (account_id),
    instrument_code TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    quantity TEXT NOT NULL,
    total_cost TEXT NOT NULL,
    avg_cost TEXT NOT NULL,
    currency TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    PRIMARY KEY (batch_id, portfolio_id, book_id, account_id, instrument_code, engine_version)
);

CREATE INDEX IF NOT EXISTS ix_book_position_snapshot_batch
ON book_position_snapshot (batch_id, engine_version, portfolio_id, book_id);

CREATE TABLE IF NOT EXISTS position_snapshot (
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    snapshot_date TEXT NOT NULL,
    instrument_code TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    quantity TEXT NOT NULL,
    total_cost TEXT NOT NULL,
    avg_cost TEXT NOT NULL,
    currency TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    PRIMARY KEY (batch_id, instrument_code, engine_version)
);

CREATE INDEX IF NOT EXISTS ix_position_snapshot_batch
ON position_snapshot (batch_id, engine_version);

CREATE TABLE IF NOT EXISTS batch_reconciliation (
    batch_id TEXT NOT NULL REFERENCES import_batch (batch_id) ON DELETE CASCADE,
    engine_version TEXT NOT NULL,
    transaction_count INTEGER NOT NULL,
    dividend_receipt_count INTEGER NOT NULL,
    corporate_action_count INTEGER NOT NULL,
    source_record_count INTEGER NOT NULL,
    mapping_count INTEGER NOT NULL,
    snapshot_count INTEGER NOT NULL,
    issue_count INTEGER NOT NULL,
    has_errors INTEGER NOT NULL,
    issues_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (batch_id, engine_version)
);
