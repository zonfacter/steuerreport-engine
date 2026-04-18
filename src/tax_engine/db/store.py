from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any


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
                conn.row_factory = sqlite3.Row
                schema_sql = (Path(__file__).with_name("migration_v1.sql")).read_text(encoding="utf-8")
                conn.executescript(schema_sql)
                self._ensure_column(
                    conn=conn,
                    table_name="processing_queue",
                    column_name="current_step",
                    column_ddl="TEXT NOT NULL DEFAULT ''",
                )
                self._ensure_column(
                    conn=conn,
                    table_name="processing_queue",
                    column_name="error_message",
                    column_ddl="TEXT",
                )
                self._ensure_column(
                    conn=conn,
                    table_name="processing_queue",
                    column_name="result_json",
                    column_ddl="TEXT",
                )
                conn.commit()
            self._initialized = True

    @staticmethod
    def _ensure_column(
        conn: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_ddl: str,
    ) -> None:
        existing_columns = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table_name})")
        }
        if column_name in existing_columns:
            return
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_ddl}")

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

    def create_processing_job(
        self,
        job_id: str,
        tax_year: int,
        ruleset_id: str,
        config_hash: str,
        status: str,
        progress: int,
    ) -> None:
        now_utc = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO processing_queue (
                    job_id,
                    tax_year,
                    ruleset_id,
                    config_hash,
                    status,
                    progress,
                    current_step,
                    error_message,
                    result_json,
                    created_at_utc,
                    updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    tax_year,
                    ruleset_id,
                    config_hash,
                    status,
                    progress,
                    "queued",
                    None,
                    None,
                    now_utc,
                    now_utc,
                ),
            )
            conn.commit()

    def update_processing_job_state(
        self,
        job_id: str,
        status: str,
        progress: int,
        current_step: str,
        error_message: str | None = None,
        result_json: str | None = None,
    ) -> bool:
        now_utc = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE processing_queue
                SET
                    status = ?,
                    progress = ?,
                    current_step = ?,
                    error_message = ?,
                    result_json = ?,
                    updated_at_utc = ?
                WHERE job_id = ?
                """,
                (status, progress, current_step, error_message, result_json, now_utc, job_id),
            )
            conn.commit()
            return cur.rowcount == 1

    def claim_next_queued_job(self) -> dict[str, Any] | None:
        now_utc = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT job_id
                FROM processing_queue
                WHERE status = 'queued'
                ORDER BY created_at_utc ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                conn.commit()
                return None

            job_id = str(row["job_id"])
            conn.execute(
                """
                UPDATE processing_queue
                SET status = ?, progress = ?, current_step = ?, error_message = NULL, result_json = NULL, updated_at_utc = ?
                WHERE job_id = ?
                """,
                ("running", 10, "load_events", now_utc, job_id),
            )
            conn.commit()
            return self.get_processing_job(job_id)

    def list_raw_events(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT unique_event_id, source_file_id, row_index, payload_json
                FROM raw_events
                ORDER BY source_file_id ASC, row_index ASC
                """
            ).fetchall()
        return [
            {
                "unique_event_id": row["unique_event_id"],
                "source_file_id": row["source_file_id"],
                "row_index": int(row["row_index"]),
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]

    def get_processing_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    job_id,
                    tax_year,
                    ruleset_id,
                    config_hash,
                    status,
                    progress,
                    current_step,
                    error_message,
                    result_json,
                    created_at_utc,
                    updated_at_utc
                FROM processing_queue
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "job_id": row["job_id"],
            "tax_year": int(row["tax_year"]),
            "ruleset_id": row["ruleset_id"],
            "config_hash": row["config_hash"],
            "status": row["status"],
            "progress": int(row["progress"]),
            "current_step": row["current_step"],
            "error_message": row["error_message"],
            "result_summary": json.loads(row["result_json"]) if row["result_json"] else None,
            "created_at_utc": row["created_at_utc"],
            "updated_at_utc": row["updated_at_utc"],
        }

    def reset_for_tests(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM processing_queue")
            conn.execute("DELETE FROM audit_trail")
            conn.execute("DELETE FROM raw_events")
            conn.execute("DELETE FROM source_files")
            conn.commit()

    def count_audit_entries(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM audit_trail").fetchone()
        return int(row["cnt"])
