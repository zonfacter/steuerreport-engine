#!/usr/bin/env python3
"""Audit TRC20 transfers for a Tron address via public Trongrid endpoints."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

TRONGRID_ACCOUNT_TRC20 = "https://api.trongrid.io/v1/accounts/{address}/transactions/trc20"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", required=True)
    parser.add_argument("--contract", default="", help="Optional TRC20 contract address, e.g. USDT on Tron")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--raw-out", required=True)
    parser.add_argument("--summary-out", required=True)
    args = parser.parse_args()

    transfers = fetch_transfers(
        address=args.address,
        contract=args.contract.strip(),
        limit=args.limit,
        sleep_seconds=args.sleep,
    )
    summary = summarize_transfers(args.address, transfers)
    raw_payload = {
        "address": args.address,
        "contract": args.contract.strip() or None,
        "fetched_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "count": len(transfers),
        "data": transfers,
    }

    Path(args.raw_out).write_text(json.dumps(raw_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(args.summary_out).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def fetch_transfers(*, address: str, contract: str, limit: int, sleep_seconds: float) -> list[dict[str, Any]]:
    transfers: list[dict[str, Any]] = []
    fingerprint = ""
    seen_ids: set[str] = set()
    while True:
        params: dict[str, str | int] = {
            "limit": limit,
            "only_confirmed": "true",
        }
        if contract:
            params["contract_address"] = contract
        if fingerprint:
            params["fingerprint"] = fingerprint
        url = TRONGRID_ACCOUNT_TRC20.format(address=urllib.parse.quote(address)) + "?" + urllib.parse.urlencode(params)
        body = get_json(url)
        batch = body.get("data") or []
        for row in batch:
            tx_id = str(row.get("transaction_id") or "")
            key = f"{tx_id}:{row.get('from')}:{row.get('to')}:{row.get('value')}"
            if key in seen_ids:
                continue
            seen_ids.add(key)
            transfers.append(row)
        next_fingerprint = str((body.get("meta") or {}).get("fingerprint") or "")
        if not next_fingerprint or next_fingerprint == fingerprint or not batch:
            break
        fingerprint = next_fingerprint
        time.sleep(sleep_seconds)
    return transfers


def get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "steuerreport-audit/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def summarize_transfers(address: str, transfers: list[dict[str, Any]]) -> dict[str, Any]:
    sorted_rows = sorted(transfers, key=lambda row: int(row.get("block_timestamp") or 0))
    rows: list[dict[str, Any]] = []
    totals: dict[str, dict[str, float]] = {}
    for row in sorted_rows:
        token = row.get("token_info") or {}
        symbol = str(token.get("symbol") or token.get("address") or "UNKNOWN")
        decimals = int(token.get("decimals") or 0)
        amount = int(row.get("value") or 0) / (10**decimals)
        direction = "in" if row.get("to") == address else "out" if row.get("from") == address else "related"
        totals.setdefault(symbol, {"in": 0.0, "out": 0.0, "related": 0.0})
        totals[symbol][direction] += amount
        rows.append(
            {
                "timestamp_utc": dt.datetime.fromtimestamp(
                    int(row.get("block_timestamp") or 0) / 1000, tz=dt.UTC
                ).isoformat(),
                "symbol": symbol,
                "amount": amount,
                "direction": direction,
                "from": row.get("from"),
                "to": row.get("to"),
                "tx_id": row.get("transaction_id"),
            }
        )
    return {
        "address": address,
        "count": len(rows),
        "first_timestamp_utc": rows[0]["timestamp_utc"] if rows else None,
        "last_timestamp_utc": rows[-1]["timestamp_utc"] if rows else None,
        "totals": totals,
        "transfers": rows,
    }


if __name__ == "__main__":
    main()
