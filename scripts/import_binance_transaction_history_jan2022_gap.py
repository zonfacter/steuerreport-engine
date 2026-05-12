#!/usr/bin/env python3
"""Import missing Binance transaction-history ledger rows for the Jan 2022 Pionex funding gap."""

from __future__ import annotations

import json
import sys
from datetime import UTC
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.service import confirm_import

SOURCE_XLSX = (
    ROOT
    / "usertransfer"
    / "Binance"
    / "export 2021"
    / "Binance-Transaction-History-202605061835(UTC+2)_344d77e2.xlsx"
)
SOURCE_NAME = "binance_transaction_history_jan2022_gap_2026-05-08"
JSON_OUT = ROOT / "var" / "binance_transaction_history_jan2022_gap_import_2026-05-08.json"
MD_OUT = ROOT / "docs" / "67_BINANCE_TRANSACTION_HISTORY_JAN2022_GAP_IMPORT_2026-05-08.md"


def main() -> None:
    rows = build_rows()
    result = confirm_import(SOURCE_NAME, rows)
    payload = {
        "source_xlsx": str(SOURCE_XLSX),
        "source_name": SOURCE_NAME,
        "row_count": len(rows),
        "import_result": result,
        "rows": rows,
        "note": "Narrow import of transaction-ledger rows only; withdrawals/deposits are intentionally excluded to avoid duplicates with Binance API transfers.",
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(render_md(payload), encoding="utf-8")
    print(json.dumps({"json": str(JSON_OUT), "md": str(MD_OUT), "import": result}, ensure_ascii=False, indent=2))


def build_rows() -> list[dict[str, Any]]:
    df = pd.read_excel(SOURCE_XLSX, sheet_name=0, header=9)
    df["Time_dt"] = pd.to_datetime(df["Time"], format="%y-%m-%d %H:%M:%S", errors="coerce")

    # File timestamps are UTC+2. This window is UTC+2 and ends before the Binance withdrawal to Pionex.
    start_local = pd.Timestamp("2022-01-01 00:00:00")
    end_local = pd.Timestamp("2022-01-19 14:52:45")
    df = df[(df["Time_dt"] >= start_local) & (df["Time_dt"] < end_local)].copy()

    wanted_ops = {
        "Transaction Revenue": ("trade", "in"),
        "Transaction Spend": ("trade", "out"),
        "Transaction Sold": ("trade", "out"),
        "Transaction Buy": ("trade", "in"),
        "Transaction Fee": ("fee", "out"),
    }
    out: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        operation = str(row.get("Operation") or "").strip()
        if operation not in wanted_ops:
            continue
        coin = str(row.get("Coin") or "").upper().strip()
        if not coin:
            continue
        change = pd.to_numeric(row.get("Change"), errors="coerce")
        if pd.isna(change) or change == 0:
            continue
        event_type, side = wanted_ops[operation]
        local_ts = row["Time_dt"]
        utc_ts = (local_ts - pd.Timedelta(hours=2)).to_pydatetime().replace(tzinfo=UTC).isoformat()
        qty = abs(change)
        time_key = local_ts.strftime("%Y%m%dT%H%M%S")
        out.append(
            {
                "timestamp_utc": utc_ts,
                "asset": coin,
                "quantity": format(qty, "f"),
                "price": "",
                "fee": "",
                "fee_asset": "",
                "side": side,
                "event_type": event_type,
                "tx_id": f"binance-txhist-jan2022:{time_key}:{idx}:{operation}:{coin}",
                "source": "binance",
                "raw_row": {
                    "source_file": str(SOURCE_XLSX),
                    "time_utc_plus_2": str(row.get("Time") or ""),
                    "account": str(row.get("Account") or ""),
                    "operation": operation,
                    "coin": coin,
                    "change": str(row.get("Change") or ""),
                    "remark": "" if pd.isna(row.get("Remark")) else str(row.get("Remark")),
                    "import_scope": "jan2022_gap_before_pionex_withdrawal",
                },
            }
        )
    out.sort(key=lambda item: (item["timestamp_utc"], item["tx_id"]))
    return out


def render_md(payload: dict[str, Any]) -> str:
    rows = payload["rows"]
    by_asset: dict[str, float] = {}
    for row in rows:
        sign = 1 if row["side"] == "in" else -1
        by_asset[row["asset"]] = by_asset.get(row["asset"], 0.0) + sign * float(row["quantity"])
    lines = [
        "# Binance Transaction History Jan 2022 Gap Import - 2026-05-08",
        "",
        "## Zweck",
        "",
        "Eng begrenzter Primaerimport aus dem Binance `Transaction History` Export, um die USDT-Luecke vor dem Pionex-Transfer am `2022-01-19` zu pruefen.",
        "",
        "## Import",
        "",
        f"- Quelle: `{payload['source_xlsx']}`",
        f"- Source Name: `{payload['source_name']}`",
        f"- Normalisierte Ledger-Zeilen: `{len(rows)}`",
        f"- Inserted Events: `{payload['import_result']['inserted_events']}`",
        f"- Duplicate Events: `{payload['import_result']['duplicate_events']}`",
        "- Ausgeschlossen: Withdrawals/Deposits, damit Binance-API-Transfers nicht dupliziert werden.",
        "",
        "## Netto nach Asset",
        "",
    ]
    for asset, value in sorted(by_asset.items()):
        lines.append(f"- `{asset}`: `{value:.12f}`")
    lines.extend(
        [
            "",
            "## Hinweis",
            "",
            "Die Ledger-Zeilen kommen aus Binance Transaction History und enthalten keine Order-IDs. Deshalb wurden deterministische `tx_id` Werte mit Zeit, Zeilenindex, Operation und Coin erzeugt. Der Import ist absichtlich auf Januar 2022 bis direkt vor die Pionex-Auszahlung begrenzt.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
