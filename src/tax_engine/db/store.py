from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4


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
                table_info = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='processing_queue'"
                ).fetchone()
                if table_info is not None:
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
                    self._ensure_column(
                        conn=conn,
                        table_name="processing_queue",
                        column_name="ruleset_version",
                        column_ddl="TEXT NOT NULL DEFAULT ''",
                    )
                    self._ensure_column(
                        conn=conn,
                        table_name="processing_queue",
                        column_name="config_json",
                        column_ddl="TEXT NOT NULL DEFAULT '{}'",
                    )
                schema_sql = (Path(__file__).with_name("migration_v1.sql")).read_text(encoding="utf-8")
                conn.executescript(schema_sql)
                self._ensure_column(
                    conn=conn,
                    table_name="tax_lines",
                    column_name="lot_source_event_id",
                    column_ddl="TEXT NOT NULL DEFAULT ''",
                )
                self._ensure_column(
                    conn=conn,
                    table_name="tax_lines",
                    column_name="transfer_chain_id",
                    column_ddl="TEXT NOT NULL DEFAULT ''",
                )
                self._ensure_column(
                    conn=conn,
                    table_name="tax_lines",
                    column_name="tax_domain",
                    column_ddl="TEXT NOT NULL DEFAULT 'private_veraeusserung'",
                )
                self._ensure_column(
                    conn=conn,
                    table_name="tax_lines",
                    column_name="lot_domain",
                    column_ddl="TEXT NOT NULL DEFAULT 'private'",
                )
                self._ensure_table_if_missing(
                    conn=conn,
                    table_name="ruleset_catalog",
                    ddl="""
                        CREATE TABLE ruleset_catalog (
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
                        )
                    """,
                )
                self._ensure_column(
                    conn=conn,
                    table_name="ruleset_catalog",
                    column_name="other_services_exemption_limit",
                    column_ddl="TEXT NOT NULL DEFAULT '256.00'",
                )
                self._ensure_table_if_missing(
                    conn=conn,
                    table_name="report_integrity",
                    ddl="""
                        CREATE TABLE report_integrity (
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
                        )
                    """,
                )
                self._ensure_table_if_missing(
                    conn=conn,
                    table_name="report_snapshots",
                    ddl="""
                        CREATE TABLE report_snapshots (
                            snapshot_id TEXT PRIMARY KEY,
                            job_id TEXT NOT NULL,
                            created_at_utc TEXT NOT NULL,
                            notes TEXT,
                            payload_json TEXT NOT NULL,
                            summary_json TEXT NOT NULL,
                            FOREIGN KEY (job_id) REFERENCES processing_queue(job_id)
                        )
                    """,
                )
                self._ensure_table_if_missing(
                    conn=conn,
                    table_name="solscan_transactions",
                    ddl="""
                        CREATE TABLE solscan_transactions (
                            signature TEXT PRIMARY KEY,
                            wallet_address TEXT NOT NULL DEFAULT '',
                            endpoint TEXT NOT NULL,
                            http_status INTEGER NOT NULL,
                            success INTEGER NOT NULL DEFAULT 0,
                            block_time_utc TEXT NOT NULL DEFAULT '',
                            slot INTEGER,
                            raw_json TEXT NOT NULL,
                            summary_json TEXT NOT NULL DEFAULT '{}',
                            fetched_at_utc TEXT NOT NULL,
                            updated_at_utc TEXT NOT NULL
                        )
                    """,
                )
                self._ensure_table_if_missing(
                    conn=conn,
                    table_name="solscan_account_transactions",
                    ddl="""
                        CREATE TABLE solscan_account_transactions (
                            wallet_address TEXT NOT NULL,
                            signature TEXT NOT NULL,
                            slot INTEGER,
                            block_time_utc TEXT NOT NULL DEFAULT '',
                            status TEXT NOT NULL DEFAULT '',
                            raw_json TEXT NOT NULL,
                            discovered_at_utc TEXT NOT NULL,
                            updated_at_utc TEXT NOT NULL,
                            PRIMARY KEY (wallet_address, signature)
                        )
                    """,
                )
                self._ensure_table_if_missing(
                    conn=conn,
                    table_name="solscan_account_transfers",
                    ddl="""
                        CREATE TABLE solscan_account_transfers (
                            transfer_id TEXT PRIMARY KEY,
                            wallet_address TEXT NOT NULL,
                            signature TEXT NOT NULL,
                            block_time_utc TEXT NOT NULL DEFAULT '',
                            flow TEXT NOT NULL DEFAULT '',
                            activity_type TEXT NOT NULL DEFAULT '',
                            token_address TEXT NOT NULL DEFAULT '',
                            token_decimals INTEGER,
                            amount TEXT NOT NULL DEFAULT '',
                            value_usd TEXT NOT NULL DEFAULT '',
                            from_address TEXT NOT NULL DEFAULT '',
                            to_address TEXT NOT NULL DEFAULT '',
                            raw_json TEXT NOT NULL,
                            discovered_at_utc TEXT NOT NULL,
                            updated_at_utc TEXT NOT NULL
                        )
                    """,
                )
                self._ensure_table_if_missing(
                    conn=conn,
                    table_name="product_position_events",
                    ddl="""
                        product_position_events (
                            event_id TEXT PRIMARY KEY,
                            platform TEXT NOT NULL,
                            product_type TEXT NOT NULL,
                            product_id TEXT NOT NULL DEFAULT '',
                            position_id TEXT NOT NULL DEFAULT '',
                            event_type TEXT NOT NULL,
                            tax_treatment TEXT NOT NULL,
                            asset TEXT NOT NULL,
                            quantity TEXT NOT NULL,
                            timestamp_utc TEXT NOT NULL,
                            source_ref TEXT NOT NULL DEFAULT '',
                            raw_json TEXT NOT NULL,
                            created_at_utc TEXT NOT NULL,
                            updated_at_utc TEXT NOT NULL
                        )
                    """,
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_solscan_transactions_wallet ON solscan_transactions(wallet_address)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_solscan_transactions_block_time ON solscan_transactions(block_time_utc)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_solscan_transactions_success ON solscan_transactions(success)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_solscan_account_transactions_wallet_time ON solscan_account_transactions(wallet_address, block_time_utc)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_solscan_account_transfers_wallet_time ON solscan_account_transfers(wallet_address, block_time_utc)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_solscan_account_transfers_signature ON solscan_account_transfers(signature)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_product_position_events_platform_time ON product_position_events(platform, timestamp_utc)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_product_position_events_asset_time ON product_position_events(asset, timestamp_utc)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_product_position_events_tax_treatment ON product_position_events(tax_treatment)")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS settings (
                        setting_key TEXT PRIMARY KEY,
                        value_json TEXT NOT NULL,
                        is_secret INTEGER NOT NULL DEFAULT 0,
                        updated_at_utc TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
            self._initialized = True

    def _ensure_table_if_missing(self, conn: sqlite3.Connection, table_name: str, ddl: str) -> None:
        table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        if table_exists is not None:
            return
        conn.execute(f"CREATE TABLE {ddl.strip()}")

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
        ruleset_version: str | None,
        config_hash: str,
        config_json: str,
        status: str,
        progress: int,
    ) -> None:
        now_utc = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            normalized_ruleset_version = str(ruleset_version or "")
            conn.execute(
                """
                INSERT INTO processing_queue (
                    job_id,
                    tax_year,
                    ruleset_id,
                    ruleset_version,
                    config_hash,
                    config_json,
                    status,
                    progress,
                    current_step,
                    error_message,
                    result_json,
                    created_at_utc,
                    updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    tax_year,
                    ruleset_id,
                    normalized_ruleset_version,
                    config_hash,
                    config_json,
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

    def upsert_product_position_events(self, events: list[dict[str, Any]]) -> dict[str, int]:
        now_utc = datetime.now(UTC).isoformat()
        inserted = 0
        updated = 0
        with self._lock, self._connect() as conn:
            for event in events:
                event_id = str(event.get("event_id") or "").strip()
                if not event_id:
                    continue
                raw_payload = event.get("raw")
                raw_json = json.dumps(raw_payload if isinstance(raw_payload, dict) else event, sort_keys=True, ensure_ascii=False)
                existing = conn.execute(
                    "SELECT 1 FROM product_position_events WHERE event_id = ?",
                    (event_id,),
                ).fetchone()
                conn.execute(
                    """
                    INSERT INTO product_position_events (
                        event_id,
                        platform,
                        product_type,
                        product_id,
                        position_id,
                        event_type,
                        tax_treatment,
                        asset,
                        quantity,
                        timestamp_utc,
                        source_ref,
                        raw_json,
                        created_at_utc,
                        updated_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(event_id) DO UPDATE SET
                        platform = excluded.platform,
                        product_type = excluded.product_type,
                        product_id = excluded.product_id,
                        position_id = excluded.position_id,
                        event_type = excluded.event_type,
                        tax_treatment = excluded.tax_treatment,
                        asset = excluded.asset,
                        quantity = excluded.quantity,
                        timestamp_utc = excluded.timestamp_utc,
                        source_ref = excluded.source_ref,
                        raw_json = excluded.raw_json,
                        updated_at_utc = excluded.updated_at_utc
                    """,
                    (
                        event_id,
                        str(event.get("platform") or "").strip().lower(),
                        str(event.get("product_type") or "").strip(),
                        str(event.get("product_id") or "").strip(),
                        str(event.get("position_id") or "").strip(),
                        str(event.get("event_type") or "").strip(),
                        str(event.get("tax_treatment") or "").strip(),
                        str(event.get("asset") or "").strip().upper(),
                        str(event.get("quantity") or "0"),
                        str(event.get("timestamp_utc") or ""),
                        str(event.get("source_ref") or ""),
                        raw_json,
                        now_utc,
                        now_utc,
                    ),
                )
                if existing is None:
                    inserted += 1
                else:
                    updated += 1
            conn.commit()
        return {"inserted": inserted, "updated": updated, "total": inserted + updated}

    def list_product_position_events(
        self,
        *,
        platform: str | None = None,
        asset: str | None = None,
        tax_treatment: str | None = None,
        limit: int = 10000,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if platform:
            clauses.append("platform = ?")
            params.append(str(platform).strip().lower())
        if asset:
            clauses.append("asset = ?")
            params.append(str(asset).strip().upper())
        if tax_treatment:
            clauses.append("tax_treatment = ?")
            params.append(str(tax_treatment).strip())
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(max(1, int(limit)))
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    event_id,
                    platform,
                    product_type,
                    product_id,
                    position_id,
                    event_type,
                    tax_treatment,
                    asset,
                    quantity,
                    timestamp_utc,
                    source_ref,
                    raw_json,
                    created_at_utc,
                    updated_at_utc
                FROM product_position_events
                {where_sql}
                ORDER BY timestamp_utc ASC, event_id ASC
                LIMIT ?
                """,
                params,
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            try:
                raw = json.loads(str(row["raw_json"]))
            except Exception:
                raw = {}
            result.append(
                {
                    "event_id": str(row["event_id"]),
                    "platform": str(row["platform"]),
                    "product_type": str(row["product_type"]),
                    "product_id": str(row["product_id"]),
                    "position_id": str(row["position_id"]),
                    "event_type": str(row["event_type"]),
                    "tax_treatment": str(row["tax_treatment"]),
                    "asset": str(row["asset"]),
                    "quantity": str(row["quantity"]),
                    "timestamp_utc": str(row["timestamp_utc"]),
                    "source_ref": str(row["source_ref"]),
                    "raw": raw,
                    "created_at_utc": str(row["created_at_utc"]),
                    "updated_at_utc": str(row["updated_at_utc"]),
                }
            )
        return result

    def list_distinct_transaction_ids(
        self,
        *,
        source: str | None = None,
        wallet_address: str | None = None,
        limit: int = 100000,
    ) -> list[str]:
        signature_expr = """COALESCE(
                    json_extract(payload_json, '$.tx_id'),
                    json_extract(payload_json, '$.signature'),
                    json_extract(payload_json, '$.transaction_hash')
                )"""
        filters: list[str] = []
        args: list[Any] = []
        if source:
            filters.append("json_extract(payload_json, '$.source') = ?")
            args.append(source)
        if wallet_address:
            filters.append("json_extract(payload_json, '$.wallet_address') = ?")
            args.append(wallet_address)
        filters.append(f"{signature_expr} IS NOT NULL")
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        safe_limit = max(1, min(int(limit), 1000000))
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT DISTINCT {signature_expr} AS signature
                FROM raw_events
                {where}
                ORDER BY signature
                LIMIT ?
                """,
                (*args, safe_limit),
            ).fetchall()
        return [str(row["signature"]).strip() for row in rows if str(row["signature"] or "").strip()]

    def upsert_solscan_transaction(
        self,
        *,
        signature: str,
        wallet_address: str,
        endpoint: str,
        http_status: int,
        success: bool,
        block_time_utc: str,
        slot: int | None,
        raw_json: str,
        summary_json: str,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO solscan_transactions (
                    signature,
                    wallet_address,
                    endpoint,
                    http_status,
                    success,
                    block_time_utc,
                    slot,
                    raw_json,
                    summary_json,
                    fetched_at_utc,
                    updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(signature) DO UPDATE SET
                    wallet_address = excluded.wallet_address,
                    endpoint = excluded.endpoint,
                    http_status = excluded.http_status,
                    success = excluded.success,
                    block_time_utc = excluded.block_time_utc,
                    slot = excluded.slot,
                    raw_json = excluded.raw_json,
                    summary_json = excluded.summary_json,
                    updated_at_utc = excluded.updated_at_utc
                """,
                (
                    signature,
                    wallet_address,
                    endpoint,
                    int(http_status),
                    1 if success else 0,
                    block_time_utc,
                    slot,
                    raw_json,
                    summary_json,
                    now,
                    now,
                ),
            )
            conn.commit()

    def get_solscan_transaction(self, signature: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    signature,
                    wallet_address,
                    endpoint,
                    http_status,
                    success,
                    block_time_utc,
                    slot,
                    raw_json,
                    summary_json,
                    fetched_at_utc,
                    updated_at_utc
                FROM solscan_transactions
                WHERE signature = ?
                """,
                (signature,),
            ).fetchone()
        if row is None:
            return None
        return {
            "signature": str(row["signature"]),
            "wallet_address": str(row["wallet_address"]),
            "endpoint": str(row["endpoint"]),
            "http_status": int(row["http_status"]),
            "success": bool(int(row["success"])),
            "block_time_utc": str(row["block_time_utc"] or ""),
            "slot": row["slot"],
            "raw": json.loads(str(row["raw_json"])),
            "summary": json.loads(str(row["summary_json"] or "{}")),
            "fetched_at_utc": str(row["fetched_at_utc"]),
            "updated_at_utc": str(row["updated_at_utc"]),
        }

    def list_solscan_transactions(self, limit: int = 1000) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 100000))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    signature,
                    wallet_address,
                    endpoint,
                    http_status,
                    success,
                    block_time_utc,
                    slot,
                    summary_json,
                    fetched_at_utc,
                    updated_at_utc
                FROM solscan_transactions
                ORDER BY block_time_utc DESC, updated_at_utc DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "signature": str(row["signature"]),
                "wallet_address": str(row["wallet_address"]),
                "endpoint": str(row["endpoint"]),
                "http_status": int(row["http_status"]),
                "success": bool(int(row["success"])),
                "block_time_utc": str(row["block_time_utc"] or ""),
                "slot": row["slot"],
                "summary": json.loads(str(row["summary_json"] or "{}")),
                "fetched_at_utc": str(row["fetched_at_utc"]),
                "updated_at_utc": str(row["updated_at_utc"]),
            }
            for row in rows
        ]

    def upsert_solscan_account_transaction(
        self,
        *,
        wallet_address: str,
        signature: str,
        slot: int | None,
        block_time_utc: str,
        status: str,
        raw_json: str,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO solscan_account_transactions (
                    wallet_address,
                    signature,
                    slot,
                    block_time_utc,
                    status,
                    raw_json,
                    discovered_at_utc,
                    updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(wallet_address, signature) DO UPDATE SET
                    slot = excluded.slot,
                    block_time_utc = excluded.block_time_utc,
                    status = excluded.status,
                    raw_json = excluded.raw_json,
                    updated_at_utc = excluded.updated_at_utc
                """,
                (wallet_address, signature, slot, block_time_utc, status, raw_json, now, now),
            )
            conn.commit()

    def upsert_solscan_account_transfer(
        self,
        *,
        transfer_id: str,
        wallet_address: str,
        signature: str,
        block_time_utc: str,
        flow: str,
        activity_type: str,
        token_address: str,
        token_decimals: int | None,
        amount: str,
        value_usd: str,
        from_address: str,
        to_address: str,
        raw_json: str,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO solscan_account_transfers (
                    transfer_id,
                    wallet_address,
                    signature,
                    block_time_utc,
                    flow,
                    activity_type,
                    token_address,
                    token_decimals,
                    amount,
                    value_usd,
                    from_address,
                    to_address,
                    raw_json,
                    discovered_at_utc,
                    updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(transfer_id) DO UPDATE SET
                    wallet_address = excluded.wallet_address,
                    signature = excluded.signature,
                    block_time_utc = excluded.block_time_utc,
                    flow = excluded.flow,
                    activity_type = excluded.activity_type,
                    token_address = excluded.token_address,
                    token_decimals = excluded.token_decimals,
                    amount = excluded.amount,
                    value_usd = excluded.value_usd,
                    from_address = excluded.from_address,
                    to_address = excluded.to_address,
                    raw_json = excluded.raw_json,
                    updated_at_utc = excluded.updated_at_utc
                """,
                (
                    transfer_id,
                    wallet_address,
                    signature,
                    block_time_utc,
                    flow,
                    activity_type,
                    token_address,
                    token_decimals,
                    amount,
                    value_usd,
                    from_address,
                    to_address,
                    raw_json,
                    now,
                    now,
                ),
            )
            conn.commit()

    def count_solscan_account_transactions(self, wallet_address: str | None = None) -> int:
        args: list[Any] = []
        where = ""
        if wallet_address:
            where = "WHERE wallet_address = ?"
            args.append(wallet_address)
        with self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) AS count FROM solscan_account_transactions {where}", args).fetchone()
        return int(row["count"] if row else 0)

    def count_solscan_account_transfers(self, wallet_address: str | None = None) -> int:
        args: list[Any] = []
        where = ""
        if wallet_address:
            where = "WHERE wallet_address = ?"
            args.append(wallet_address)
        with self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) AS count FROM solscan_account_transfers {where}", args).fetchone()
        return int(row["count"] if row else 0)

    def list_solscan_account_signatures(self, wallet_address: str, limit: int = 1000000) -> list[str]:
        safe_limit = max(1, min(int(limit), 1000000))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT signature
                FROM solscan_account_transactions
                WHERE wallet_address = ?
                ORDER BY block_time_utc DESC, signature ASC
                LIMIT ?
                """,
                (wallet_address, safe_limit),
            ).fetchall()
        return [str(row["signature"]) for row in rows]

    def list_source_file_summaries(self, limit: int = 200) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 5000))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    sf.source_file_id,
                    sf.source_name,
                    sf.row_count AS declared_row_count,
                    sf.created_at_utc,
                    COUNT(re.unique_event_id) AS imported_event_count
                FROM source_files sf
                LEFT JOIN raw_events re ON re.source_file_id = sf.source_file_id
                GROUP BY sf.source_file_id, sf.source_name, sf.row_count, sf.created_at_utc
                ORDER BY sf.created_at_utc DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "source_file_id": row["source_file_id"],
                "source_name": row["source_name"],
                "declared_row_count": int(row["declared_row_count"] or 0),
                "imported_event_count": int(row["imported_event_count"] or 0),
                "created_at_utc": row["created_at_utc"],
            }
            for row in rows
        ]

    def list_processing_jobs(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 5000))
        safe_offset = max(0, int(offset))
        conditions: list[str] = []
        args: list[Any] = []

        if status:
            conditions.append("p.status = ?")
            args.append(str(status).strip())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        args.extend([safe_limit, safe_offset])

        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    p.job_id,
                    p.tax_year,
                    p.ruleset_id,
                    p.ruleset_version,
                    p.config_json,
                    p.status,
                    p.progress,
                    p.current_step,
                    p.error_message,
                    p.created_at_utc,
                    p.updated_at_utc,
                    COALESCE(tc.tax_line_count, 0) AS tax_line_count,
                    COALESCE(dc.derivative_line_count, 0) AS derivative_line_count
                FROM processing_queue p
                LEFT JOIN (
                    SELECT job_id, COUNT(*) AS tax_line_count
                    FROM tax_lines
                    GROUP BY job_id
                ) AS tc ON tc.job_id = p.job_id
                LEFT JOIN (
                    SELECT job_id, COUNT(*) AS derivative_line_count
                    FROM derivative_lines
                    GROUP BY job_id
                ) AS dc ON dc.job_id = p.job_id
                {where_clause}
                ORDER BY p.updated_at_utc DESC
                LIMIT ?
                OFFSET ?
                """,
                tuple(args),
            ).fetchall()
        return [
            {
                "job_id": row["job_id"],
                "tax_year": int(row["tax_year"]),
                "ruleset_id": row["ruleset_id"],
                "ruleset_version": str(row["ruleset_version"] or ""),
                "config": json.loads(row["config_json"] or "{}"),
                "status": row["status"],
                "progress": int(row["progress"]),
                "current_step": row["current_step"],
                "error_message": row["error_message"],
                "created_at_utc": row["created_at_utc"],
                "updated_at_utc": row["updated_at_utc"],
                "tax_line_count": int(row["tax_line_count"] or 0),
                "derivative_line_count": int(row["derivative_line_count"] or 0),
            }
            for row in rows
        ]

    def replace_tax_lines(self, job_id: str, tax_lines: list[dict[str, Any]]) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM tax_lines WHERE job_id = ?", (job_id,))
            for idx, line in enumerate(tax_lines, start=1):
                conn.execute(
                    """
                    INSERT INTO tax_lines (
                        job_id,
                        line_no,
                        asset,
                        qty,
                        buy_timestamp_utc,
                        sell_timestamp_utc,
                        cost_basis_eur,
                        proceeds_eur,
                        gain_loss_eur,
                        hold_days,
                        tax_status,
                        tax_domain,
                        lot_domain,
                        source_event_id,
                        lot_source_event_id,
                        transfer_chain_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        idx,
                        str(line["asset"]),
                        str(line["qty"]),
                        str(line["buy_timestamp_utc"]),
                        str(line["sell_timestamp_utc"]),
                        str(line["cost_basis_eur"]),
                        str(line["proceeds_eur"]),
                        str(line["gain_loss_eur"]),
                        int(line["hold_days"]),
                        str(line["tax_status"]),
                        str(line.get("tax_domain", "private_veraeusserung")),
                        str(line.get("lot_domain", "private")),
                        str(line["source_event_id"]),
                        str(line.get("lot_source_event_id", "")),
                        str(line.get("transfer_chain_id", "")),
                    ),
                )
            conn.commit()

    def get_tax_lines(self, job_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    line_no,
                    asset,
                    qty,
                    buy_timestamp_utc,
                    sell_timestamp_utc,
                    cost_basis_eur,
                    proceeds_eur,
                    gain_loss_eur,
                    hold_days,
                    tax_status,
                    tax_domain,
                    lot_domain,
                    source_event_id,
                    lot_source_event_id,
                    transfer_chain_id
                FROM tax_lines
                WHERE job_id = ?
                ORDER BY line_no ASC
                """,
                (job_id,),
            ).fetchall()
        return [
            {
                "line_no": int(row["line_no"]),
                "asset": row["asset"],
                "qty": row["qty"],
                "buy_timestamp_utc": row["buy_timestamp_utc"],
                "sell_timestamp_utc": row["sell_timestamp_utc"],
                "cost_basis_eur": row["cost_basis_eur"],
                "proceeds_eur": row["proceeds_eur"],
                "gain_loss_eur": row["gain_loss_eur"],
                "hold_days": int(row["hold_days"]),
                "tax_status": row["tax_status"],
                "tax_domain": row["tax_domain"],
                "lot_domain": row["lot_domain"],
                "source_event_id": row["source_event_id"],
                "lot_source_event_id": row["lot_source_event_id"],
                "transfer_chain_id": row["transfer_chain_id"],
            }
            for row in rows
        ]

    def get_tax_line(self, job_id: str, line_no: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    line_no,
                    asset,
                    qty,
                    buy_timestamp_utc,
                    sell_timestamp_utc,
                    cost_basis_eur,
                    proceeds_eur,
                    gain_loss_eur,
                hold_days,
                tax_status,
                tax_domain,
                lot_domain,
                source_event_id,
                    lot_source_event_id,
                    transfer_chain_id
                FROM tax_lines
                WHERE job_id = ? AND line_no = ?
                """,
                (job_id, line_no),
            ).fetchone()
        if row is None:
            return None
        return {
            "line_no": int(row["line_no"]),
            "asset": row["asset"],
            "qty": row["qty"],
            "buy_timestamp_utc": row["buy_timestamp_utc"],
            "sell_timestamp_utc": row["sell_timestamp_utc"],
            "cost_basis_eur": row["cost_basis_eur"],
            "proceeds_eur": row["proceeds_eur"],
            "gain_loss_eur": row["gain_loss_eur"],
            "hold_days": int(row["hold_days"]),
            "tax_status": row["tax_status"],
            "tax_domain": row["tax_domain"],
            "lot_domain": row["lot_domain"],
            "source_event_id": row["source_event_id"],
            "lot_source_event_id": row["lot_source_event_id"],
            "transfer_chain_id": row["transfer_chain_id"],
        }

    def get_raw_event(self, unique_event_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    re.unique_event_id,
                    re.source_file_id,
                    re.row_index,
                    re.payload_json,
                    re.created_at_utc,
                    sf.source_name,
                    sf.source_hash
                FROM raw_events re
                LEFT JOIN source_files sf
                    ON sf.source_file_id = re.source_file_id
                WHERE re.unique_event_id = ?
                """,
                (unique_event_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "unique_event_id": row["unique_event_id"],
            "source_file_id": row["source_file_id"],
            "source_name": row["source_name"],
            "source_hash": row["source_hash"],
            "row_index": int(row["row_index"]),
            "created_at_utc": row["created_at_utc"],
            "payload": json.loads(row["payload_json"]),
        }

    def replace_derivative_lines(self, job_id: str, derivative_lines: list[dict[str, Any]]) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM derivative_lines WHERE job_id = ?", (job_id,))
            for idx, line in enumerate(derivative_lines, start=1):
                conn.execute(
                    """
                    INSERT INTO derivative_lines (
                        job_id,
                        line_no,
                        position_id,
                        asset,
                        event_type,
                        open_timestamp_utc,
                        close_timestamp_utc,
                        collateral_eur,
                        proceeds_eur,
                        fees_eur,
                        funding_eur,
                        gain_loss_eur,
                        loss_bucket,
                        source_event_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        idx,
                        str(line["position_id"]),
                        str(line["asset"]),
                        str(line["event_type"]),
                        str(line["open_timestamp_utc"]),
                        str(line["close_timestamp_utc"]),
                        str(line["collateral_eur"]),
                        str(line["proceeds_eur"]),
                        str(line["fees_eur"]),
                        str(line["funding_eur"]),
                        str(line["gain_loss_eur"]),
                        str(line["loss_bucket"]),
                        str(line["source_event_id"]),
                    ),
                )
            conn.commit()

    def get_derivative_lines(self, job_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    line_no,
                    position_id,
                    asset,
                    event_type,
                    open_timestamp_utc,
                    close_timestamp_utc,
                    collateral_eur,
                    proceeds_eur,
                    fees_eur,
                    funding_eur,
                    gain_loss_eur,
                    loss_bucket,
                    source_event_id
                FROM derivative_lines
                WHERE job_id = ?
                ORDER BY line_no ASC
                """,
                (job_id,),
            ).fetchall()
        return [
            {
                "line_no": int(row["line_no"]),
                "position_id": row["position_id"],
                "asset": row["asset"],
                "event_type": row["event_type"],
                "open_timestamp_utc": row["open_timestamp_utc"],
                "close_timestamp_utc": row["close_timestamp_utc"],
                "collateral_eur": row["collateral_eur"],
                "proceeds_eur": row["proceeds_eur"],
                "fees_eur": row["fees_eur"],
                "funding_eur": row["funding_eur"],
                "gain_loss_eur": row["gain_loss_eur"],
                "loss_bucket": row["loss_bucket"],
                "source_event_id": row["source_event_id"],
            }
            for row in rows
        ]

    def upsert_ruleset_catalog(self, payload: dict[str, Any]) -> None:
        ruleset_id = str(payload.get("ruleset_id", "")).strip()
        ruleset_version = str(payload.get("ruleset_version", "")).strip()
        jurisdiction = str(payload.get("jurisdiction", "")).strip()
        valid_from = str(payload.get("valid_from", "")).strip()
        valid_to = str(payload.get("valid_to", "")).strip()
        exemption_limit_so = str(payload.get("exemption_limit_so", "")).strip()
        other_services_exemption_limit = str(payload.get("other_services_exemption_limit", "256.00")).strip() or "256.00"
        holding_period_months = int(payload.get("holding_period_months", 0))
        staking_extension = 1 if bool(payload.get("staking_extension", False)) else 0
        mining_tax_category = str(payload.get("mining_tax_category", "")).strip()
        status = str(payload.get("status", "draft")).strip() or "draft"
        source_hash = str(payload.get("source_hash", "manual")).strip() or "manual"
        approved_by = payload.get("approved_by")
        notes = payload.get("notes")

        if not (
            ruleset_id
            and ruleset_version
            and jurisdiction
            and valid_from
            and valid_to
            and exemption_limit_so
            and holding_period_months >= 0
            and mining_tax_category
        ):
            raise ValueError("invalid ruleset payload")

        now_utc = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ruleset_catalog (
                    ruleset_id,
                    ruleset_version,
                    jurisdiction,
                    valid_from,
                    valid_to,
                    exemption_limit_so,
                    other_services_exemption_limit,
                    holding_period_months,
                    staking_extension,
                    mining_tax_category,
                    status,
                    source_hash,
                    approved_by,
                    notes,
                    created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ruleset_id, ruleset_version) DO UPDATE SET
                    jurisdiction = excluded.jurisdiction,
                    valid_from = excluded.valid_from,
                    valid_to = excluded.valid_to,
                    exemption_limit_so = excluded.exemption_limit_so,
                    other_services_exemption_limit = excluded.other_services_exemption_limit,
                    holding_period_months = excluded.holding_period_months,
                    staking_extension = excluded.staking_extension,
                    mining_tax_category = excluded.mining_tax_category,
                    status = excluded.status,
                    source_hash = excluded.source_hash,
                    approved_by = excluded.approved_by,
                    notes = excluded.notes
                """,
                (
                    ruleset_id,
                    ruleset_version,
                    jurisdiction,
                    valid_from,
                    valid_to,
                    exemption_limit_so,
                    other_services_exemption_limit,
                    holding_period_months,
                    staking_extension,
                    mining_tax_category,
                    status,
                    source_hash,
                    str(approved_by) if approved_by is not None else None,
                    str(notes) if notes is not None else None,
                    now_utc,
                ),
            )
            conn.commit()

    def list_rulesets(self, include_pending: bool = True) -> list[dict[str, Any]]:
        if include_pending:
            sql = """
                SELECT
                    ruleset_id,
                    ruleset_version,
                    jurisdiction,
                    valid_from,
                    valid_to,
                    exemption_limit_so,
                    other_services_exemption_limit,
                    holding_period_months,
                    staking_extension,
                    mining_tax_category,
                    status,
                    source_hash,
                    approved_by,
                    notes,
                    created_at_utc
                FROM ruleset_catalog
                ORDER BY jurisdiction ASC, ruleset_id ASC, ruleset_version ASC
            """
            args: tuple[Any, ...] = ()
        else:
            sql = """
                SELECT
                    ruleset_id,
                    ruleset_version,
                    jurisdiction,
                    valid_from,
                    valid_to,
                    exemption_limit_so,
                    other_services_exemption_limit,
                    holding_period_months,
                    staking_extension,
                    mining_tax_category,
                    status,
                    source_hash,
                    approved_by,
                    notes,
                    created_at_utc
                FROM ruleset_catalog
                WHERE status IN ('approved', 'active')
                ORDER BY jurisdiction ASC, ruleset_id ASC, ruleset_version ASC
            """
            args = ()

        with self._connect() as conn:
            rows = conn.execute(sql, args).fetchall()
        return [
            {
                "ruleset_id": row["ruleset_id"],
                "ruleset_version": row["ruleset_version"],
                "jurisdiction": row["jurisdiction"],
                "valid_from": row["valid_from"],
                "valid_to": row["valid_to"],
                "exemption_limit_so": row["exemption_limit_so"],
                "other_services_exemption_limit": row["other_services_exemption_limit"],
                "holding_period_months": row["holding_period_months"],
                "staking_extension": int(row["staking_extension"]),
                "mining_tax_category": row["mining_tax_category"],
                "status": row["status"],
                "source_hash": row["source_hash"],
                "approved_by": row["approved_by"],
                "notes": row["notes"],
                "created_at_utc": row["created_at_utc"],
            }
            for row in rows
        ]

    def get_ruleset(self, ruleset_id: str, ruleset_version: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    ruleset_id,
                    ruleset_version,
                    jurisdiction,
                    valid_from,
                    valid_to,
                    exemption_limit_so,
                    other_services_exemption_limit,
                    holding_period_months,
                    staking_extension,
                    mining_tax_category,
                    status,
                    source_hash,
                    approved_by,
                    notes,
                    created_at_utc
                FROM ruleset_catalog
                WHERE ruleset_id = ? AND ruleset_version = ?
                """,
                (ruleset_id, ruleset_version),
            ).fetchone()
        if row is None:
            return None
        return {
            "ruleset_id": row["ruleset_id"],
            "ruleset_version": row["ruleset_version"],
            "jurisdiction": row["jurisdiction"],
            "valid_from": row["valid_from"],
            "valid_to": row["valid_to"],
            "exemption_limit_so": row["exemption_limit_so"],
            "other_services_exemption_limit": row["other_services_exemption_limit"],
            "holding_period_months": row["holding_period_months"],
            "staking_extension": int(row["staking_extension"]),
            "mining_tax_category": row["mining_tax_category"],
            "status": row["status"],
            "source_hash": row["source_hash"],
            "approved_by": row["approved_by"],
            "notes": row["notes"],
            "created_at_utc": row["created_at_utc"],
        }

    def insert_report_integrity(
        self,
        job_id: str,
        data_hash: str,
        ruleset_id: str,
        ruleset_version: str,
        ruleset_hash: str,
        config_hash: str,
        report_integrity_id: str,
        event_count: int,
        run_started_at_utc: str,
    ) -> None:
        now_utc = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO report_integrity (
                    job_id,
                    run_started_at_utc,
                    data_hash,
                    ruleset_id,
                    ruleset_version,
                    ruleset_hash,
                    config_hash,
                    report_integrity_id,
                    event_count,
                    created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    run_started_at_utc = excluded.run_started_at_utc,
                    data_hash = excluded.data_hash,
                    ruleset_id = excluded.ruleset_id,
                    ruleset_version = excluded.ruleset_version,
                    ruleset_hash = excluded.ruleset_hash,
                    config_hash = excluded.config_hash,
                    report_integrity_id = excluded.report_integrity_id,
                    event_count = excluded.event_count
                """,
                (
                    job_id,
                    run_started_at_utc,
                    data_hash,
                    ruleset_id,
                    ruleset_version,
                    ruleset_hash,
                    config_hash,
                    report_integrity_id,
                    event_count,
                    now_utc,
                ),
            )
            conn.commit()

    def get_report_integrity(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    job_id,
                    run_started_at_utc,
                    data_hash,
                    ruleset_id,
                    ruleset_version,
                    ruleset_hash,
                    config_hash,
                    report_integrity_id,
                    event_count,
                    created_at_utc
                FROM report_integrity
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "job_id": row["job_id"],
            "run_started_at_utc": row["run_started_at_utc"],
            "data_hash": row["data_hash"],
            "ruleset_id": row["ruleset_id"],
            "ruleset_version": row["ruleset_version"],
            "ruleset_hash": row["ruleset_hash"],
            "config_hash": row["config_hash"],
            "report_integrity_id": row["report_integrity_id"],
            "event_count": int(row["event_count"]),
            "created_at_utc": row["created_at_utc"],
        }

    def create_report_snapshot(
        self,
        job_id: str,
        payload_json: str,
        summary_json: str,
        notes: str | None = None,
    ) -> str:
        snapshot_id = str(uuid4())
        created_at_utc = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO report_snapshots (
                    snapshot_id,
                    job_id,
                    created_at_utc,
                    notes,
                    payload_json,
                    summary_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    job_id,
                    created_at_utc,
                    str(notes).strip() if isinstance(notes, str) else None,
                    payload_json,
                    summary_json,
                ),
            )
            conn.commit()
        return snapshot_id

    def get_report_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    snapshot_id,
                    job_id,
                    created_at_utc,
                    notes,
                    payload_json,
                    summary_json
                FROM report_snapshots
                WHERE snapshot_id = ?
                """,
                (snapshot_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "snapshot_id": row["snapshot_id"],
            "job_id": row["job_id"],
            "created_at_utc": row["created_at_utc"],
            "notes": row["notes"],
            "payload_json": row["payload_json"],
            "summary_json": row["summary_json"],
        }

    def list_jobs_using_event(self, unique_event_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT job_id
                FROM (
                    SELECT job_id FROM tax_lines WHERE source_event_id = ?
                    UNION
                    SELECT job_id FROM derivative_lines WHERE source_event_id = ?
                )
                ORDER BY job_id ASC
                """,
                (unique_event_id, unique_event_id),
            ).fetchall()
        return [{"job_id": row["job_id"]} for row in rows]

    def create_transfer_match(
        self,
        outbound_event_id: str,
        inbound_event_id: str,
        confidence_score: str,
        time_diff_seconds: int,
        amount_diff: str,
        status: str,
        method: str,
        note: str | None = None,
    ) -> str:
        match_id = str(uuid4())
        created_at_utc = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO transfer_matches (
                    match_id,
                    outbound_event_id,
                    inbound_event_id,
                    confidence_score,
                    time_diff_seconds,
                    amount_diff,
                    status,
                    method,
                    note,
                    created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    match_id,
                    outbound_event_id,
                    inbound_event_id,
                    confidence_score,
                    time_diff_seconds,
                    amount_diff,
                    status,
                    method,
                    note,
                    created_at_utc,
                ),
            )
            conn.commit()
        return match_id

    def list_transfer_matches(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    match_id,
                    outbound_event_id,
                    inbound_event_id,
                    confidence_score,
                    time_diff_seconds,
                    amount_diff,
                    status,
                    method,
                    note,
                    created_at_utc
                FROM transfer_matches
                ORDER BY created_at_utc ASC
                """
            ).fetchall()
        return [
            {
                "match_id": row["match_id"],
                "outbound_event_id": row["outbound_event_id"],
                "inbound_event_id": row["inbound_event_id"],
                "confidence_score": row["confidence_score"],
                "time_diff_seconds": int(row["time_diff_seconds"]),
                "amount_diff": row["amount_diff"],
                "status": row["status"],
                "method": row["method"],
                "note": row["note"],
                "created_at_utc": row["created_at_utc"],
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
                    ruleset_version,
                    config_hash,
                    config_json,
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
            "ruleset_version": str(row["ruleset_version"] or ""),
            "config_hash": row["config_hash"],
            "config": json.loads(row["config_json"] or "{}"),
            "status": row["status"],
            "progress": int(row["progress"]),
            "current_step": row["current_step"],
            "error_message": row["error_message"],
            "result_summary": json.loads(row["result_json"]) if row["result_json"] else None,
            "tax_line_count": self.count_tax_lines(row["job_id"]),
            "derivative_line_count": self.count_derivative_lines(row["job_id"]),
            "created_at_utc": row["created_at_utc"],
            "updated_at_utc": row["updated_at_utc"],
        }

    def get_latest_processing_job(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT job_id
                FROM processing_queue
                ORDER BY updated_at_utc DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return self.get_processing_job(str(row["job_id"]))

    def count_tax_lines(self, job_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM tax_lines WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return int(row["cnt"])

    def count_derivative_lines(self, job_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM derivative_lines WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return int(row["cnt"])

    def reset_for_tests(self) -> None:
        if os.getenv("STEUERREPORT_ENV") != "testing":
            raise PermissionError(
                "reset_for_tests() called outside of testing environment. "
                "Set STEUERREPORT_ENV=testing and use a dedicated test database."
            )
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM product_position_events")
            conn.execute("DELETE FROM solscan_account_transfers")
            conn.execute("DELETE FROM solscan_account_transactions")
            conn.execute("DELETE FROM solscan_transactions")
            conn.execute("DELETE FROM fx_cache")
            conn.execute("DELETE FROM settings")
            conn.execute("DELETE FROM transfer_matches")
            conn.execute("DELETE FROM report_snapshots")
            conn.execute("DELETE FROM report_integrity")
            conn.execute("DELETE FROM ruleset_catalog")
            conn.execute("DELETE FROM derivative_lines")
            conn.execute("DELETE FROM tax_lines")
            conn.execute("DELETE FROM processing_queue")
            conn.execute("DELETE FROM audit_trail")
            conn.execute("DELETE FROM raw_events")
            conn.execute("DELETE FROM source_files")
            conn.commit()

    def count_audit_entries(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM audit_trail").fetchone()
        return int(row["cnt"])

    def upsert_setting(self, setting_key: str, value_json: str, is_secret: bool) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO settings (setting_key, value_json, is_secret, updated_at_utc)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET
                    value_json = excluded.value_json,
                    is_secret = excluded.is_secret,
                    updated_at_utc = excluded.updated_at_utc
                """,
                (setting_key, value_json, 1 if is_secret else 0, datetime.now(UTC).isoformat()),
            )
            conn.commit()

    def get_setting(self, setting_key: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT setting_key, value_json, is_secret, updated_at_utc
                FROM settings
                WHERE setting_key = ?
                """,
                (setting_key,),
            ).fetchone()
        if row is None:
            return None
        return {
            "setting_key": str(row["setting_key"]),
            "value_json": str(row["value_json"]),
            "is_secret": bool(int(row["is_secret"])),
            "updated_at_utc": str(row["updated_at_utc"]),
        }

    def list_settings(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT setting_key, value_json, is_secret, updated_at_utc
                FROM settings
                ORDER BY setting_key ASC
                """
            ).fetchall()
        return [
            {
                "setting_key": str(row["setting_key"]),
                "value_json": str(row["value_json"]),
                "is_secret": bool(int(row["is_secret"])),
                "updated_at_utc": str(row["updated_at_utc"]),
            }
            for row in rows
        ]

    def get_fx_rate(self, rate_date: str, base_ccy: str, quote_ccy: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    rate_date,
                    base_ccy,
                    quote_ccy,
                    rate,
                    source,
                    source_rate_date,
                    updated_at_utc
                FROM fx_cache
                WHERE rate_date = ? AND base_ccy = ? AND quote_ccy = ?
                """,
                (rate_date, base_ccy.upper(), quote_ccy.upper()),
            ).fetchone()
        if row is None:
            return None
        return {
            "rate_date": str(row["rate_date"]),
            "base_ccy": str(row["base_ccy"]),
            "quote_ccy": str(row["quote_ccy"]),
            "rate": str(row["rate"]),
            "source": str(row["source"]),
            "source_rate_date": str(row["source_rate_date"] or ""),
            "updated_at_utc": str(row["updated_at_utc"]),
        }

    def list_fx_rates(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    rate_date,
                    base_ccy,
                    quote_ccy,
                    rate,
                    source,
                    source_rate_date,
                    updated_at_utc
                FROM fx_cache
                ORDER BY base_ccy, quote_ccy, rate_date
                """
            ).fetchall()
        return [
            {
                "rate_date": str(row["rate_date"]),
                "base_ccy": str(row["base_ccy"]),
                "quote_ccy": str(row["quote_ccy"]),
                "rate": str(row["rate"]),
                "source": str(row["source"]),
                "source_rate_date": str(row["source_rate_date"] or ""),
                "updated_at_utc": str(row["updated_at_utc"]),
            }
            for row in rows
        ]

    def get_fx_rate_on_or_before(self, rate_date: str, base_ccy: str, quote_ccy: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    rate_date,
                    base_ccy,
                    quote_ccy,
                    rate,
                    source,
                    source_rate_date,
                    updated_at_utc
                FROM fx_cache
                WHERE rate_date <= ? AND base_ccy = ? AND quote_ccy = ?
                ORDER BY rate_date DESC
                LIMIT 1
                """,
                (rate_date, base_ccy.upper(), quote_ccy.upper()),
            ).fetchone()
        if row is None:
            return None
        return {
            "rate_date": str(row["rate_date"]),
            "base_ccy": str(row["base_ccy"]),
            "quote_ccy": str(row["quote_ccy"]),
            "rate": str(row["rate"]),
            "source": str(row["source"]),
            "source_rate_date": str(row["source_rate_date"] or ""),
            "updated_at_utc": str(row["updated_at_utc"]),
        }

    def upsert_fx_rate(
        self,
        rate_date: str,
        base_ccy: str,
        quote_ccy: str,
        rate: str,
        source: str,
        source_rate_date: str | None,
    ) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO fx_cache (
                    rate_date,
                    base_ccy,
                    quote_ccy,
                    rate,
                    source,
                    source_rate_date,
                    updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(rate_date, base_ccy, quote_ccy) DO UPDATE SET
                    rate = excluded.rate,
                    source = excluded.source,
                    source_rate_date = excluded.source_rate_date,
                    updated_at_utc = excluded.updated_at_utc
                """,
                (
                    rate_date,
                    base_ccy.upper(),
                    quote_ccy.upper(),
                    rate,
                    source,
                    source_rate_date,
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()
