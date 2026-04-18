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
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_events_source_file_id ON raw_events(source_file_id);
CREATE INDEX IF NOT EXISTS idx_audit_trace_id ON audit_trail(trace_id);
CREATE INDEX IF NOT EXISTS idx_processing_queue_status ON processing_queue(status);
