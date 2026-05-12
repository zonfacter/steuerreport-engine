#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.service import confirm_import  # noqa: E402
from tax_engine.ingestion.store import STORE  # noqa: E402

RUN_DATE = "2026-05-10"
DEDUPE_JSON = ROOT / "var" / f"binance_earn_reward_dedupe_{RUN_DATE}.json"
JSON_PATH = ROOT / "var" / f"binance_earn_unmatched_reward_import_{RUN_DATE}.json"
DOC_PATH = ROOT / "docs" / f"203_BINANCE_EARN_UNMATCHED_REWARD_IMPORT_{RUN_DATE}.md"


def main() -> None:
    audit = json.loads(DEDUPE_JSON.read_text(encoding="utf-8"))
    rows = [normalize_row(row) for row in audit.get("unmatched", []) if isinstance(row, dict)]
    if rows:
        import_result = confirm_import("binance_earn_unmatched_rewards_2026_api_2026-05-10", rows)
        report_rows = rows
        mode = "imported_from_current_dedupe"
    else:
        report_rows = list_existing_imported_rows()
        import_result = {
            "source_file_id": "",
            "source_created": False,
            "inserted_events": 0,
            "duplicate_events": 0,
            "event_ids": [],
            "existing_imported_events": len(report_rows),
        }
        mode = "reported_existing_imports"
    result = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_audit": str(DEDUPE_JSON.relative_to(ROOT)),
        "mode": mode,
        "row_count": len(report_rows),
        "rows": report_rows,
        "import_result": import_result,
    }
    JSON_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    DOC_PATH.write_text(render_doc(result), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "import": import_result}, indent=2, ensure_ascii=False))


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    event_id = str(row.get("event_id") or "").strip()
    asset = str(row.get("asset") or "").upper()
    quantity = str(row.get("quantity") or "0")
    timestamp_utc = str(row.get("timestamp_utc") or "")
    product_type = str(row.get("product_type") or "")
    tx_id = f"binance-earn-unmatched:{event_id}"
    return {
        "timestamp_utc": timestamp_utc,
        "asset": asset,
        "quantity": quantity,
        "price": "",
        "fee": "0",
        "fee_asset": "",
        "side": "in",
        "event_type": "interest",
        "tx_id": tx_id,
        "source": "binance_api",
        "source_endpoint": product_type,
        "reward_type": product_type,
        "product_position_event_id": event_id,
        "raw_row": {
            "product_position_event_id": event_id,
            "product_type": product_type,
            "product_id": str(row.get("product_id") or ""),
            "source_ref": str(row.get("source_ref") or ""),
            "source_audit": str(DEDUPE_JSON.relative_to(ROOT)),
        },
    }


def list_existing_imported_rows() -> list[dict[str, Any]]:
    STORE.initialize()
    rows: list[dict[str, Any]] = []
    for event in STORE.list_raw_events():
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        if raw_row.get("source_audit") != str(DEDUPE_JSON.relative_to(ROOT)):
            continue
        if not str(payload.get("product_position_event_id") or raw_row.get("product_position_event_id") or "").startswith("binance_earn:"):
            continue
        rows.append(
            {
                "timestamp_utc": str(payload.get("timestamp_utc") or ""),
                "asset": str(payload.get("asset") or "").upper(),
                "quantity": str(payload.get("quantity") or "0"),
                "price": str(payload.get("price") or ""),
                "fee": str(payload.get("fee") or "0"),
                "fee_asset": str(payload.get("fee_asset") or ""),
                "side": str(payload.get("side") or ""),
                "event_type": str(payload.get("event_type") or ""),
                "tx_id": str(payload.get("tx_id") or ""),
                "source": str(payload.get("source") or ""),
                "source_endpoint": str(payload.get("source_endpoint") or ""),
                "reward_type": str(payload.get("reward_type") or ""),
                "product_position_event_id": str(payload.get("product_position_event_id") or raw_row.get("product_position_event_id") or ""),
                "unique_event_id": str(event.get("unique_event_id") or ""),
                "source_file_id": str(event.get("source_file_id") or ""),
            }
        )
    return sorted(rows, key=lambda item: (item["timestamp_utc"], item["asset"], item["quantity"]))


def render_doc(result: dict[str, Any]) -> str:
    totals: dict[str, Decimal] = {}
    counts: dict[str, int] = {}
    for row in result.get("rows", []):
        asset = str(row.get("asset") or "")
        counts[asset] = counts.get(asset, 0) + 1
        totals[asset] = totals.get(asset, Decimal("0")) + Decimal(str(row.get("quantity") or "0"))
    lines = [
        "# Binance Earn Unmatched Reward Import",
        "",
        f"Stand: {result['created_at_utc']}",
        "",
        f"Quelle: `{result['source_audit']}`",
        "",
        "## Import",
        "",
        f"- Modus: `{result.get('mode', '')}`",
        f"- Zeilen: `{result['row_count']}`",
        f"- Eingefuegte Events: `{result['import_result'].get('inserted_events', 0)}`",
        f"- Duplikate: `{result['import_result'].get('duplicate_events', 0)}`",
        f"- Bereits vorhandene Events: `{result['import_result'].get('existing_imported_events', 0)}`",
        f"- Source file id: `{result['import_result'].get('source_file_id', '')}`",
        "",
        "## Mengen",
        "",
        "| Asset | Anzahl | Menge |",
        "|---|---:|---:|",
    ]
    for asset in sorted(totals):
        lines.append(f"| `{asset}` | `{counts[asset]}` | `{totals[asset].to_eng_string()}` |")
    lines.extend(
        [
            "",
            "## Steuerliche Einordnung",
            "",
            "- Importiert wurden nur Reward-Kandidaten, die im Dedupe-Audit nicht bereits in `raw_events` vorhanden waren.",
            "- Typ: `interest`, `side=in`, Quelle: `binance_api`.",
            "- EUR-Bewertung/Preisanker bleibt Aufgabe des Preisbackfills; die Rohmenge ist jetzt steuerlich sichtbar und zugleich ueber `product_position_event_id` zum Produktpositionsbeleg rueckverfolgbar.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
