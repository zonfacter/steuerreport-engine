PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_files (
    source_file_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_events (
    unique_event_id TEXT PRIMARY KEY,
    source_file_id TEXT NOT NULL,
    row_index INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY(source_file_id) REFERENCES source_files(source_file_id)
);

CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    action TEXT NOT NULL,
    event_time_utc TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processing_queue (
    job_id TEXT PRIMARY KEY,
    tax_year INTEGER NOT NULL,
    ruleset_id TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL,
    current_step TEXT NOT NULL DEFAULT '',
    error_message TEXT,
    result_json TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tax_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    line_no INTEGER NOT NULL,
    asset TEXT NOT NULL,
    qty TEXT NOT NULL,
    buy_timestamp_utc TEXT NOT NULL,
    sell_timestamp_utc TEXT NOT NULL,
    cost_basis_eur TEXT NOT NULL,
    proceeds_eur TEXT NOT NULL,
    gain_loss_eur TEXT NOT NULL,
    hold_days INTEGER NOT NULL,
    tax_status TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES processing_queue(job_id)
);

CREATE TABLE IF NOT EXISTS derivative_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    line_no INTEGER NOT NULL,
    position_id TEXT NOT NULL,
    asset TEXT NOT NULL,
    event_type TEXT NOT NULL,
    open_timestamp_utc TEXT NOT NULL,
    close_timestamp_utc TEXT NOT NULL,
    collateral_eur TEXT NOT NULL,
    proceeds_eur TEXT NOT NULL,
    fees_eur TEXT NOT NULL,
    funding_eur TEXT NOT NULL,
    gain_loss_eur TEXT NOT NULL,
    loss_bucket TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES processing_queue(job_id)
);

CREATE TABLE IF NOT EXISTS transfer_matches (
    match_id TEXT PRIMARY KEY,
    outbound_event_id TEXT NOT NULL,
    inbound_event_id TEXT NOT NULL,
    confidence_score TEXT NOT NULL,
    time_diff_seconds INTEGER NOT NULL,
    amount_diff TEXT NOT NULL,
    status TEXT NOT NULL,
    method TEXT NOT NULL,
    note TEXT,
    created_at_utc TEXT NOT NULL,
    UNIQUE(outbound_event_id, inbound_event_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_events_source_file_id ON raw_events(source_file_id);
CREATE INDEX IF NOT EXISTS idx_audit_trace_id ON audit_trail(trace_id);
CREATE INDEX IF NOT EXISTS idx_processing_queue_status ON processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_tax_lines_job_id ON tax_lines(job_id);
CREATE INDEX IF NOT EXISTS idx_derivative_lines_job_id ON derivative_lines(job_id);
CREATE INDEX IF NOT EXISTS idx_transfer_matches_status ON transfer_matches(status);
