from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tax_engine.ingestion.service import confirm_import

KNOWN_FUNGIBLE_ASSETS = {"SOL", "USDC", "USDT", "JUP", "HNT", "IOT", "MOBILE", "ZEUS"}
SAFE_CLASSES = {"dex_swap_or_route", "transfer_in_or_airdrop"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import safe rows from a Solscan missing-event preview.")
    parser.add_argument("--preview-json", required=True)
    parser.add_argument("--source-name", default="")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    preview = json.loads(Path(args.preview_json).read_text(encoding="utf-8"))
    rows, excluded = select_safe_rows(preview)
    source_name = args.source_name or f"solscan_wallet_discovery_safe_{preview['wallet_address'][:6]}_2026-05-08"

    summary: dict[str, Any] = {
        "source_name": source_name,
        "execute": bool(args.execute),
        "selected_rows": len(rows),
        "selected_signatures": len({str(row.get("tx_id") or "") for row in rows}),
        "excluded_signatures": len(excluded),
        "excluded_by_reason": dict(Counter(item["reason"] for item in excluded)),
        "selected_by_event_type": dict(Counter(str(row.get("event_type") or "") for row in rows)),
        "selected_by_asset": dict(Counter(str(row.get("asset") or "") for row in rows)),
    }
    if args.execute:
        summary["import_result"] = confirm_import(source_name=source_name, rows=rows)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


def select_safe_rows(preview: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    by_signature: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in preview.get("proposed_rows") or []:
        if isinstance(row, dict):
            by_signature[str(row.get("tx_id") or "")].append(row)

    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for signature, rows in sorted(by_signature.items()):
        if not signature or not rows:
            continue
        classes = {str((row.get("raw_row") or {}).get("classification") or "") for row in rows}
        assets = {str(row.get("asset") or "") for row in rows}
        if not classes <= SAFE_CLASSES:
            excluded.append({"signature": signature, "reason": "unsafe_class"})
            continue
        if not assets <= KNOWN_FUNGIBLE_ASSETS:
            excluded.append({"signature": signature, "reason": "unknown_or_nonfungible_asset"})
            continue
        selected.extend(rows)
    return selected, excluded


if __name__ == "__main__":
    main()
