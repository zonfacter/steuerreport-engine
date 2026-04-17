PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    ruleset_id TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed'))
);

CREATE TABLE IF NOT EXISTS ingestion_events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    depot_id TEXT NOT NULL,
    source_system TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    asset_in TEXT,
    amount_in TEXT,
    asset_out TEXT,
    amount_out TEXT,
    fee_asset TEXT,
    fee_amount TEXT,
    payload_json TEXT NOT NULL,
    unique_event_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ingestion_unique_event
    ON ingestion_events(run_id, unique_event_id);

CREATE TABLE IF NOT EXISTS fifo_lots (
    lot_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    depot_id TEXT NOT NULL,
    asset_symbol TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    quantity_open TEXT NOT NULL,
    quantity_total TEXT NOT NULL,
    cost_basis_eur TEXT NOT NULL,
    source_event_id TEXT NOT NULL REFERENCES ingestion_events(event_id)
);

CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    disposal_event_id TEXT NOT NULL REFERENCES ingestion_events(event_id),
    acquisition_lot_id TEXT NOT NULL REFERENCES fifo_lots(lot_id),
    matched_quantity TEXT NOT NULL,
    proceeds_eur TEXT NOT NULL,
    cost_basis_eur TEXT NOT NULL,
    gain_loss_eur TEXT NOT NULL,
    holding_period_days INTEGER NOT NULL,
    decision_reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processing_queue (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    event_id TEXT NOT NULL REFERENCES ingestion_events(event_id) ON DELETE CASCADE,
    priority INTEGER NOT NULL DEFAULT 100,
    state TEXT NOT NULL CHECK (state IN ('pending', 'processing', 'done', 'error')),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    available_at TEXT NOT NULL,
    locked_by TEXT,
    locked_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_processing_queue_state
    ON processing_queue(state, priority, available_at);

CREATE TABLE IF NOT EXISTS audit_trail (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    event_id TEXT REFERENCES ingestion_events(event_id) ON DELETE SET NULL,
    depot_id TEXT,
    action_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    decision_payload_json TEXT NOT NULL,
    rationale TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_run_event
    ON audit_trail(run_id, event_id, created_at);
