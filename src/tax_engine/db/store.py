from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock


class SQLiteImportStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lock = RLock()
        self._initialized = False

    def initialize(self) -> None:
        with self._lock:
            if self._initialized:
                return
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                schema_sql = (Path(__file__).with_name("migration_v1.sql")).read_text(encoding="utf-8")
                conn.executescript(schema_sql)
                conn.commit()
            self._initialized = True

    def _connect(self) -> sqlite3.Connection:
        self.initialize()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def upsert_source_file(
        self,
        source_file_id: str,
        source_name: str,
        source_hash: str,
        row_count: int,
    ) -> bool:
        created_at_utc = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO source_files (
                    source_file_id,
                    source_name,
                    source_hash,
                    row_count,
                    created_at_utc
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (source_file_id, source_name, source_hash, row_count, created_at_utc),
            )
            conn.commit()
            return cur.rowcount == 1

    def insert_raw_event(
        self,
        unique_event_id: str,
        source_file_id: str,
        row_index: int,
        payload_json: str,
    ) -> bool:
        created_at_utc = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO raw_events (
                    unique_event_id,
                    source_file_id,
                    row_index,
                    payload_json,
                    created_at_utc
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (unique_event_id, source_file_id, row_index, payload_json, created_at_utc),
            )
            conn.commit()
            return cur.rowcount == 1

    def write_audit(self, trace_id: str, action: str, event_time_utc: str, payload_json: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_trail (
                    trace_id,
                    action,
                    event_time_utc,
                    payload_json
                ) VALUES (?, ?, ?, ?)
                """,
                (trace_id, action, event_time_utc, payload_json),
            )
            conn.commit()

    def reset_for_tests(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM audit_trail")
            conn.execute("DELETE FROM raw_events")
            conn.execute("DELETE FROM source_files")
            conn.commit()

    def count_audit_entries(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM audit_trail").fetchone()
        return int(row["cnt"])
