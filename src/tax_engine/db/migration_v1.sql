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
    ruleset_version TEXT NOT NULL DEFAULT '',
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

CREATE TABLE IF NOT EXISTS fx_cache (
    rate_date TEXT NOT NULL,
    base_ccy TEXT NOT NULL,
    quote_ccy TEXT NOT NULL,
    rate TEXT NOT NULL,
    source TEXT NOT NULL,
    source_rate_date TEXT,
    updated_at_utc TEXT NOT NULL,
    PRIMARY KEY (rate_date, base_ccy, quote_ccy)
);

CREATE TABLE IF NOT EXISTS ruleset_catalog (
    ruleset_id TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    exemption_limit_so TEXT NOT NULL,
    other_services_exemption_limit TEXT NOT NULL DEFAULT '256.00',
    holding_period_months INTEGER NOT NULL,
    staking_extension INTEGER NOT NULL DEFAULT 0,
    mining_tax_category TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    source_hash TEXT NOT NULL,
    approved_by TEXT,
    notes TEXT,
    created_at_utc TEXT NOT NULL,
    PRIMARY KEY (ruleset_id, ruleset_version)
);

CREATE TABLE IF NOT EXISTS report_integrity (
    job_id TEXT PRIMARY KEY,
    run_started_at_utc TEXT NOT NULL,
    data_hash TEXT NOT NULL,
    ruleset_id TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    ruleset_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    report_integrity_id TEXT NOT NULL,
    event_count INTEGER NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES processing_queue(job_id)
);

CREATE TABLE IF NOT EXISTS report_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    notes TEXT,
    payload_json TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES processing_queue(job_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_events_source_file_id ON raw_events(source_file_id);
CREATE INDEX IF NOT EXISTS idx_audit_trace_id ON audit_trail(trace_id);
CREATE INDEX IF NOT EXISTS idx_processing_queue_status ON processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_processing_queue_ruleset ON processing_queue(ruleset_id, ruleset_version);
CREATE INDEX IF NOT EXISTS idx_tax_lines_job_id ON tax_lines(job_id);
CREATE INDEX IF NOT EXISTS idx_derivative_lines_job_id ON derivative_lines(job_id);
CREATE INDEX IF NOT EXISTS idx_transfer_matches_status ON transfer_matches(status);
CREATE INDEX IF NOT EXISTS idx_fx_cache_pair_date ON fx_cache(base_ccy, quote_ccy, rate_date);
CREATE INDEX IF NOT EXISTS idx_ruleset_catalog_status ON ruleset_catalog(status);
CREATE INDEX IF NOT EXISTS idx_report_integrity_ruleset ON report_integrity(ruleset_id, ruleset_version);
CREATE INDEX IF NOT EXISTS idx_report_snapshots_job_id ON report_snapshots(job_id);
