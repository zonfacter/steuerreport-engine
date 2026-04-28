#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime

from tax_engine.admin import put_admin_setting
from tax_engine.connectors.solana_service import (
    fetch_solana_wallet_full_history,
    solana_rpc_rate_snapshot,
)
from tax_engine.ingestion.service import confirm_import
from tax_engine.ingestion.store import STORE


def main() -> int:
    parser = argparse.ArgumentParser(description="Background backfill scanner for Solana wallet imports.")
    parser.add_argument("--wallet", required=True, help="Solana wallet address")
    parser.add_argument("--rpc-url", required=True, help="Primary Solana RPC URL")
    parser.add_argument("--rpc-fallbacks", default="", help="Comma separated fallback RPC URLs")
    parser.add_argument("--source-name", default="solana_wallet_background_scan", help="Import source name")
    parser.add_argument("--max-signatures", type=int, default=300, help="Signatures per batch")
    parser.add_argument("--max-batches", type=int, default=100, help="Maximum batches for one run")
    parser.add_argument("--timeout-seconds", type=int, default=25, help="RPC timeout")
    parser.add_argument("--sleep-seconds", type=float, default=0.4, help="Sleep between batches")
    parser.add_argument("--before-signature", default="", help="Optional cursor to resume from")
    parser.add_argument("--start-time-ms", type=int, default=1588291200000, help="Inclusive start time in epoch ms")
    parser.add_argument("--end-time-ms", type=int, default=0, help="Exclusive end time in epoch ms; defaults to now")
    parser.add_argument("--aggregate-jupiter", action="store_true", default=True)
    parser.add_argument("--jupiter-window-seconds", type=int, default=2)
    args = parser.parse_args()

    fallbacks = [item.strip() for item in args.rpc_fallbacks.split(",") if item.strip()]
    cursor_key = f"runtime.scan.cursor.{args.wallet}"
    stats_key = f"runtime.scan.stats.{args.wallet}"
    before_signature: str | None = args.before_signature.strip() or None
    cursor_row = STORE.get_setting(cursor_key)
    if before_signature is None and cursor_row is not None:
        try:
            loaded_cursor = json.loads(str(cursor_row.get("value_json", '""')))
            if isinstance(loaded_cursor, str) and loaded_cursor.strip():
                before_signature = loaded_cursor.strip()
        except Exception:
            pass
    end_time_ms = args.end_time_ms if args.end_time_ms > 0 else int(datetime.now(UTC).timestamp() * 1000)

    total_rows = 0
    total_inserted = 0
    total_duplicates = 0

    for batch_no in range(1, args.max_batches + 1):
        preview = fetch_solana_wallet_full_history(
            wallet_address=args.wallet,
            rpc_url=args.rpc_url,
            rpc_fallback_urls=fallbacks,
            before_signature=before_signature,
            timeout_seconds=args.timeout_seconds,
            start_time_ms=args.start_time_ms,
            end_time_ms=end_time_ms,
            max_signatures_per_call=args.max_signatures,
            max_signatures_total=args.max_signatures,
            aggregate_jupiter=args.aggregate_jupiter,
            jupiter_window_seconds=args.jupiter_window_seconds,
        )
        rows = preview.get("rows", [])
        if not isinstance(rows, list):
            rows = []
        signature_count = int(preview.get("signature_scanned_count", preview.get("signature_count", 0)))
        next_cursor = preview.get("next_before_signature")
        print(
            f"[{datetime.now(UTC).isoformat()}] batch={batch_no} signatures={signature_count} rows={len(rows)} before={before_signature}",
            flush=True,
        )
        if signature_count == 0:
            break

        import_result = confirm_import(source_name=f"{args.source_name}_batch_{batch_no:05d}", rows=rows)
        inserted = int(import_result.get("inserted_events", 0))
        duplicates = int(import_result.get("duplicate_events", 0))
        total_rows += len(rows)
        total_inserted += inserted
        total_duplicates += duplicates
        print(
            f"  imported inserted={inserted} duplicates={duplicates} source_file_id={import_result.get('source_file_id')}",
            flush=True,
        )

        if isinstance(next_cursor, str) and next_cursor.strip():
            before_signature = next_cursor.strip()
            put_admin_setting(cursor_key, before_signature, is_secret=False)

        put_admin_setting(
            stats_key,
            {
                "last_run_utc": datetime.now(UTC).isoformat(),
                "last_batch_no": batch_no,
                "total_rows": total_rows,
                "total_inserted": total_inserted,
                "total_duplicates": total_duplicates,
                "last_before_signature": before_signature,
                "rpc_rate_control": solana_rpc_rate_snapshot(),
            },
            is_secret=False,
        )
        if bool(preview.get("reached_start", False)):
            break
        time.sleep(max(args.sleep_seconds, 0))

    print(
        f"[done] rows={total_rows} inserted={total_inserted} duplicates={total_duplicates} cursor={before_signature}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
