#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE  # noqa: E402

OUT_DIR = Path.home() / ".local" / "share" / "steuerreport" / "ai_readonly"
OUT_DB = OUT_DIR / "steuerreport_ai_readonly.sqlite"
DOC_PATH = ROOT / "docs" / "204_AI_READONLY_DB_SNAPSHOT.md"

EXCLUDED_TABLES = {"settings", "audit_trail", "sqlite_sequence"}


def main() -> int:
    STORE.initialize()
    source_db = Path(STORE.db_path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp_db = OUT_DB.with_suffix(".tmp.sqlite")
    if tmp_db.exists():
        tmp_db.unlink()

    shutil.copy2(source_db, tmp_db)
    os.chmod(tmp_db, 0o600)
    with sqlite3.connect(f"file:{source_db}?mode=ro", uri=True) as src, sqlite3.connect(tmp_db) as dst:
        src.row_factory = sqlite3.Row
        dst.row_factory = sqlite3.Row
        table_names = [
            str(row["name"])
            for row in src.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            if str(row["name"]) not in EXCLUDED_TABLES
        ]
        for table in EXCLUDED_TABLES:
            if table == "sqlite_sequence":
                continue
            dst.execute(f"DROP TABLE IF EXISTS {quote_ident(table)}")
        create_ai_views(dst)
        dst.execute("VACUUM")
        dst.commit()

    if OUT_DB.exists():
        OUT_DB.unlink()
    tmp_db.replace(OUT_DB)
    os.chmod(OUT_DB, 0o444)
    write_doc(source_db, table_names)
    print({"db": str(OUT_DB), "doc": str(DOC_PATH), "size_bytes": OUT_DB.stat().st_size})
    return 0


def create_ai_views(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE VIEW ai_raw_events_flat AS
        SELECT
            unique_event_id,
            source_file_id,
            row_index,
            json_extract(payload_json, '$.timestamp_utc') AS timestamp_utc,
            json_extract(payload_json, '$.source') AS source,
            json_extract(payload_json, '$.event_type') AS event_type,
            json_extract(payload_json, '$.side') AS side,
            json_extract(payload_json, '$.asset') AS asset,
            json_extract(payload_json, '$.quantity') AS quantity,
            json_extract(payload_json, '$.price') AS price,
            json_extract(payload_json, '$.fee') AS fee,
            json_extract(payload_json, '$.fee_asset') AS fee_asset,
            json_extract(payload_json, '$.tx_id') AS tx_id,
            payload_json
        FROM raw_events;

        CREATE VIEW ai_tax_lines_flat AS
        SELECT
            tl.*,
            pq.tax_year,
            pq.ruleset_id,
            pq.status AS job_status
        FROM tax_lines tl
        LEFT JOIN processing_queue pq ON pq.job_id = tl.job_id;

        CREATE VIEW ai_latest_completed_jobs AS
        SELECT *
        FROM processing_queue
        WHERE status = 'completed'
        ORDER BY tax_year ASC, updated_at_utc DESC;

        CREATE VIEW ai_latest_completed_jobs_per_year AS
        SELECT *
        FROM (
            SELECT
                pq.*,
                row_number() OVER (
                    PARTITION BY tax_year
                    ORDER BY updated_at_utc DESC, created_at_utc DESC
                ) AS ai_rank
            FROM processing_queue pq
            WHERE status = 'completed'
        )
        WHERE ai_rank = 1;

        CREATE VIEW ai_open_zero_cost_tax_lines AS
        SELECT
            tl.*,
            pq.tax_year,
            pq.updated_at_utc AS job_updated_at_utc
        FROM tax_lines tl
        JOIN ai_latest_completed_jobs_per_year pq ON pq.job_id = tl.job_id
        WHERE CAST(tl.proceeds_eur AS REAL) > 0
          AND ABS(CAST(tl.cost_basis_eur AS REAL)) < 0.000000001;

        CREATE VIEW ai_transfer_matches_flat AS
        SELECT
            tm.*,
            out_e.payload_json AS outbound_payload_json,
            in_e.payload_json AS inbound_payload_json
        FROM transfer_matches tm
        LEFT JOIN raw_events out_e ON out_e.unique_event_id = tm.outbound_event_id
        LEFT JOIN raw_events in_e ON in_e.unique_event_id = tm.inbound_event_id;
        """
    )


def write_doc(source_db: Path, table_names: list[str]) -> None:
    lines = [
        "# AI Readonly DB Snapshot",
        "",
        f"- Quelle: `{source_db}`",
        f"- Snapshot: `{OUT_DB}`",
        "- Modus: Datei ist mit `0444` read-only gesetzt.",
        "- Nicht enthalten: `settings`, `audit_trail`, `sqlite_sequence`.",
        "- Zweck: lokale KI darf Daten analysieren, aber keine Produktivdaten oder Secrets veraendern.",
        "",
        "## Read-only Verbindung",
        "",
        "```bash",
        f"sqlite3 'file:{OUT_DB}?mode=ro&immutable=1'",
        "```",
        "",
        "## Wichtige Views",
        "",
        "- `ai_raw_events_flat`: Rohereignisse mit den wichtigsten JSON-Feldern als Spalten.",
        "- `ai_tax_lines_flat`: Tax-Lines inklusive Steuerjahr/Job-Status.",
        "- `ai_latest_completed_jobs`: abgeschlossene Jobs, chronologisch nach Steuerjahr.",
        "- `ai_latest_completed_jobs_per_year`: genau der neueste abgeschlossene Job je Steuerjahr.",
        "- `ai_open_zero_cost_tax_lines`: steuerpflichtige Zeilen aus den neuesten Jobs mit Erlös und Cost Basis 0.",
        "- `ai_transfer_matches_flat`: Transfer-Matches inklusive Outbound-/Inbound-Payload.",
        "",
        "## Kopierte Tabellen",
        "",
    ]
    lines.extend(f"- `{table}`" for table in table_names)
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


if __name__ == "__main__":
    raise SystemExit(main())
