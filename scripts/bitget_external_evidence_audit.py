#!/usr/bin/env python3
"""Collect external evidence that can support, but not replace, missing Bitget bot history."""

from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

VAR_DIR = ROOT / "var"
RAW_DIR = VAR_DIR / "external_evidence" / "bitget_public_market_2026-05-08"
JSON_PATH = VAR_DIR / "bitget_external_evidence_audit_2026-05-08.json"
DOC_PATH = ROOT / "docs" / "57_BITGET_EXTERNAL_EVIDENCE_AUDIT_2026-05-08.md"

SYMBOL_RE = re.compile(r"\b([A-Z0-9]{2,15}USDT)\b")
KNOWN_SYMBOLS = ("BTCUSDT", "SOLUSDT", "JUPUSDT", "HNTUSDT", "XRPUSDT")
BITGET_BASE = "https://api.bitget.com"


def main() -> None:
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    events = load_bitget_events()
    summary = summarize_events(events)
    fetch_result = fetch_public_market_data(summary)
    onchain_result = fetch_onchain_transfer_evidence(events)
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "scope": "External evidence for missing Bitget bot/grid/internal transaction details.",
        "important_boundary": (
            "Public market data can support price plausibility only. It cannot prove personal Bitget bot fills, "
            "internal transfers, fees, funding, liquidation, or realized PnL."
        ),
        "event_summary": summary,
        "source_assessment": source_assessment(),
        "public_market_fetch": fetch_result,
        "onchain_transfer_evidence": onchain_result,
        "raw_dir": str(RAW_DIR),
        "next_actions": [
            "Attach Bitget support response once received.",
            "If Bitget cannot provide old bot details, build a reconstruction report from balances, external flows, realized PnL, funding and fees.",
            "Use public candles only to validate timestamp/price plausibility, not to create missing trades.",
            "Keep Blockpit/WISO as reference-only search hints unless matched to primary Bitget records.",
        ],
    }
    JSON_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    write_doc(audit)
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "raw_dir": str(RAW_DIR)}, indent=2))


def load_bitget_events() -> list[dict[str, Any]]:
    raw_events = STORE.list_raw_events()
    reviewed, _summary = apply_review_actions(raw_events)
    effective, _override_count = apply_tax_event_overrides(reviewed)
    rows: list[dict[str, Any]] = []
    for event in effective:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
        text = " ".join(
            [
                str(payload.get("source") or ""),
                str(payload.get("event_type") or ""),
                json.dumps(raw_row, ensure_ascii=False)[:3000],
            ]
        ).lower()
        if "bitget" not in text:
            continue
        rows.append({"event": event, "payload": payload, "raw_row": raw_row})
    return rows


def summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_year: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    types: Counter[str] = Counter()
    assets: Counter[str] = Counter()
    symbols: Counter[str] = Counter()
    timestamps: list[str] = []
    for row in events:
        payload = row["payload"]
        raw_row = row["raw_row"]
        ts = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
        if ts:
            timestamps.append(ts)
            by_year[ts[:4]] += 1
        sources[str(payload.get("source") or "unknown")] += 1
        types[str(payload.get("event_type") or "unknown")] += 1
        assets[str(payload.get("asset") or payload.get("symbol") or "unknown").upper()] += 1
        text = json.dumps({"payload": payload, "raw_row": raw_row}, ensure_ascii=False).upper()
        for symbol in SYMBOL_RE.findall(text):
            symbols[symbol] += 1
    for symbol in KNOWN_SYMBOLS:
        if symbol not in symbols:
            symbols[symbol] = 0
    min_ts = min(timestamps) if timestamps else ""
    max_ts = max(timestamps) if timestamps else ""
    start = date_from_ts(min_ts)
    end = date_from_ts(max_ts)
    return {
        "event_count": len(events),
        "first_event_utc": min_ts,
        "last_event_utc": max_ts,
        "fetch_start_date": start,
        "fetch_end_date": end,
        "by_year": dict(sorted(by_year.items())),
        "sources": top(sources, 20),
        "event_types": top(types, 30),
        "assets": top(assets, 30),
        "symbols": top(symbols, 20),
        "target_symbols": [row["key"] for row in top(symbols, 10) if row["key"] in set(KNOWN_SYMBOLS) or row["count"] > 0],
    }


def fetch_public_market_data(summary: dict[str, Any]) -> dict[str, Any]:
    start_date = parse_date(summary["fetch_start_date"]) - timedelta(days=3)
    end_date = parse_date(summary["fetch_end_date"]) + timedelta(days=3)
    symbols = [symbol for symbol in summary["target_symbols"] if symbol.endswith("USDT")]
    result = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "symbols": {}}
    for symbol in symbols:
        result["symbols"][symbol] = {
            "spot_history_candles": fetch_candles(
                path="/api/v2/spot/market/history-candles",
                params={"symbol": symbol, "granularity": "1Dutc"},
                start_date=start_date,
                end_date=end_date,
                raw_name=f"spot_{symbol}_1Dutc.json",
            ),
            "futures_history_candles": fetch_candles(
                path="/api/v2/mix/market/history-candles",
                params={"symbol": symbol, "productType": "USDT-FUTURES", "granularity": "1Dutc"},
                start_date=start_date,
                end_date=end_date,
                raw_name=f"futures_{symbol}_1Dutc.json",
            ),
            "futures_funding_rates": fetch_funding_rates(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                raw_name=f"funding_{symbol}.json",
            ),
        }
        time.sleep(0.05)
    return result


def fetch_onchain_transfer_evidence(events: list[dict[str, Any]]) -> dict[str, Any]:
    signatures: dict[str, dict[str, Any]] = {}
    for row in events:
        payload = row["payload"]
        raw_row = row["raw_row"]
        event_type = str(payload.get("event_type") or "").lower()
        if not any(token in event_type for token in ("deposit", "withdraw", "transfer")):
            continue
        for key in ("tradeId", "signature", "txHash", "tx_hash"):
            value = raw_row.get(key) or payload.get(key)
            if isinstance(value, str) and 80 <= len(value.strip()) <= 100:
                signatures[value.strip()] = {
                    "event_timestamp_utc": payload.get("timestamp_utc") or payload.get("timestamp") or "",
                    "source": payload.get("source") or "",
                    "event_type": payload.get("event_type") or "",
                    "asset": payload.get("asset") or "",
                    "side": payload.get("side") or "",
                    "amount": payload.get("quantity") or raw_row.get("amount") or "",
                    "from_address": raw_row.get("fromAddress") or "",
                    "to_address": raw_row.get("toAddress") or "",
                    "bitget_order_id": raw_row.get("orderId") or raw_row.get("bizOrderId") or "",
                }
    records: dict[str, Any] = {}
    for signature, event_meta in signatures.items():
        raw_path = RAW_DIR / f"solana_tx_{signature}.json"
        record = {
            "signature": signature,
            "event_meta": event_meta,
            "status": "not_fetched",
            "raw_path": str(raw_path),
            "summary": {},
        }
        try:
            response = requests.post(
                "https://api.mainnet-beta.solana.com",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
                },
                timeout=20,
            )
            response.raise_for_status()
            body = response.json()
            raw_path.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
            result = body.get("result") if isinstance(body, dict) else None
            if isinstance(result, dict):
                record["status"] = "confirmed_on_solana_rpc"
                record["summary"] = summarize_solana_transaction(result)
            else:
                record["status"] = "not_found_or_unavailable"
                record["summary"] = {"rpc_error": body.get("error") if isinstance(body, dict) else body}
        except Exception as exc:
            record["status"] = "fetch_error"
            record["summary"] = {"error": f"{type(exc).__name__}: {exc}"}
        records[signature] = record
        time.sleep(0.1)
    return {
        "signature_count": len(records),
        "evidence_class": "external_flow_primary_onchain_evidence",
        "records": records,
    }


def summarize_solana_transaction(result: dict[str, Any]) -> dict[str, Any]:
    block_time = result.get("blockTime")
    meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
    tx = result.get("transaction") if isinstance(result.get("transaction"), dict) else {}
    message = tx.get("message") if isinstance(tx.get("message"), dict) else {}
    accounts = message.get("accountKeys") if isinstance(message.get("accountKeys"), list) else []
    account_keys = []
    for account in accounts[:12]:
        if isinstance(account, dict):
            account_keys.append(account.get("pubkey"))
        else:
            account_keys.append(str(account))
    token_balances = meta.get("postTokenBalances") if isinstance(meta.get("postTokenBalances"), list) else []
    return {
        "block_time_utc": datetime.fromtimestamp(int(block_time), UTC).isoformat() if block_time else "",
        "slot": result.get("slot"),
        "status": meta.get("status"),
        "err": meta.get("err"),
        "fee_lamports": meta.get("fee"),
        "account_keys_sample": account_keys,
        "post_token_mints": sorted(
            {
                str(row.get("mint"))
                for row in token_balances
                if isinstance(row, dict) and row.get("mint")
            }
        ),
    }


def fetch_candles(
    *,
    path: str,
    params: dict[str, str],
    start_date: datetime,
    end_date: datetime,
    raw_name: str,
) -> dict[str, Any]:
    candles: dict[str, list[Any]] = {}
    end_ms = int(end_date.timestamp() * 1000)
    start_ms = int(start_date.timestamp() * 1000)
    errors: list[str] = []
    for _ in range(5):
        request_params = dict(params)
        request_params.update({"endTime": str(end_ms), "limit": "200"})
        url = f"{BITGET_BASE}{path}"
        try:
            response = requests.get(url, params=request_params, timeout=15)
            response.raise_for_status()
            body = response.json()
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            break
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or not data:
            if isinstance(body, dict) and body.get("code") not in {"00000", "0", None}:
                errors.append(json.dumps(body, ensure_ascii=False)[:500])
            break
        for candle in data:
            if not isinstance(candle, list) or not candle:
                continue
            try:
                ts_ms = int(candle[0])
            except (TypeError, ValueError):
                continue
            if start_ms <= ts_ms <= int(end_date.timestamp() * 1000):
                candles[str(ts_ms)] = candle
        min_seen = min(int(row[0]) for row in data if isinstance(row, list) and row)
        if min_seen <= start_ms:
            break
        end_ms = min_seen - 1
        time.sleep(0.05)
    rows = [candles[key] for key in sorted(candles, key=int)]
    raw_path = RAW_DIR / raw_name
    raw_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "status": "ok" if rows else "empty_or_error",
        "row_count": len(rows),
        "first_ts_ms": rows[0][0] if rows else "",
        "last_ts_ms": rows[-1][0] if rows else "",
        "raw_path": str(raw_path),
        "errors": errors,
        "evidence_class": "public_market_price_plausibility_only",
    }


def fetch_funding_rates(*, symbol: str, start_date: datetime, end_date: datetime, raw_name: str) -> dict[str, Any]:
    start_ms = int(start_date.timestamp() * 1000)
    end_ms = int(end_date.timestamp() * 1000)
    rows_by_key: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for page_no in range(1, 31):
        try:
            response = requests.get(
                f"{BITGET_BASE}/api/v2/mix/market/history-fund-rate",
                params={
                    "symbol": symbol,
                    "productType": "USDT-FUTURES",
                    "pageSize": "100",
                    "pageNo": str(page_no),
                },
                timeout=15,
            )
            response.raise_for_status()
            body = response.json()
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            break
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or not data:
            if isinstance(body, dict) and body.get("code") not in {"00000", "0", None}:
                errors.append(json.dumps(body, ensure_ascii=False)[:500])
            break
        for row in data:
            if not isinstance(row, dict):
                continue
            ts = row.get("fundingTime") or row.get("fundingRateTimestamp")
            try:
                ts_ms = int(str(ts))
            except (TypeError, ValueError):
                continue
            if start_ms <= ts_ms <= end_ms:
                rows_by_key[str(ts_ms)] = row
        oldest = min(
            int(str(row.get("fundingTime") or row.get("fundingRateTimestamp")))
            for row in data
            if isinstance(row, dict) and (row.get("fundingTime") or row.get("fundingRateTimestamp"))
        )
        if oldest < start_ms:
            break
        time.sleep(0.05)
    rows = [rows_by_key[key] for key in sorted(rows_by_key, key=int)]
    raw_path = RAW_DIR / raw_name
    raw_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "status": "ok" if rows else "empty_or_error",
        "row_count": len(rows),
        "first_ts_ms": rows[0].get("fundingTime") if rows else "",
        "last_ts_ms": rows[-1].get("fundingTime") if rows else "",
        "raw_path": str(raw_path),
        "errors": errors,
        "evidence_class": "public_funding_rate_plausibility_only",
    }


def source_assessment() -> list[dict[str, Any]]:
    return [
        {
            "source": "Bitget account export / support",
            "can_prove": ["personal fund flows", "personal order/fill history if Bitget provides it", "account statements"],
            "cannot_prove": [],
            "status": "support_requested",
            "priority": "highest",
            "url": "https://www.bitget.site/support/articles/12560603824169",
        },
        {
            "source": "Bitget private API",
            "can_prove": ["recent private orders/fills/account bills inside API retention windows"],
            "cannot_prove": ["older bot fills if API retention has expired"],
            "status": "limited_by_retention",
            "priority": "high",
            "url": "https://www.bitget.com/api-doc/uta/trade/Get-Order-History",
        },
        {
            "source": "Bitget public market candles",
            "can_prove": ["market existed", "daily high/low/open/close range", "price plausibility"],
            "cannot_prove": ["personal bot fill", "fee", "funding", "liquidation attribution", "internal transfer"],
            "status": "collected_now",
            "priority": "supporting",
            "url": "https://www.bitget.com/api-doc/spot/market/Get-History-Candle-Data",
        },
        {
            "source": "Bitget public futures funding rates",
            "can_prove": ["public funding-rate environment for a futures symbol"],
            "cannot_prove": ["personal funding paid/received", "position size", "position holding interval"],
            "status": "collected_now_where_available",
            "priority": "supporting",
            "url": "https://www.bitget.com/api-doc/classic/contract/market/Get-History-Funding-Rate",
        },
        {
            "source": "On-chain explorers",
            "can_prove": ["deposits to Bitget", "withdrawals from Bitget if address/txid known"],
            "cannot_prove": ["trades inside Bitget", "bot internal rebalancing"],
            "status": "usable_for_external_flows",
            "priority": "high_for_transfers",
            "url": "https://tronscan.org/ and chain-specific explorers",
        },
        {
            "source": "Tax-tool caches such as Blockpit/CoinTracking/Koinly/Coinpanda",
            "can_prove": ["what the tool had imported at export time", "reference event list"],
            "cannot_prove": ["primary Bitget truth unless raw Bitget records are included and matchable"],
            "status": "reference_only",
            "priority": "supporting",
            "url": "https://coinpanda.io/integrations/bitget/",
        },
        {
            "source": "Tardis.dev / commercial market-data archives",
            "can_prove": ["historical public trades/order book/candles"],
            "cannot_prove": ["which trades belonged to this account or bot"],
            "status": "optional_market_reference",
            "priority": "low_for_tax_facts",
            "url": "https://docs.tardis.dev/historical-data-details/bitget",
        },
    ]


def write_doc(audit: dict[str, Any]) -> None:
    summary = audit["event_summary"]
    fetch = audit["public_market_fetch"]
    lines = [
        "# Bitget External Evidence Audit - 2026-05-08",
        "",
        "## Ergebnis",
        "",
        "Externe Quellen koennen die Bitget-Bot-Trade-Luecke nur teilweise stuetzen.",
        "Persoenliche Bot-Fills, interne Umbuchungen, konkrete Fees, Funding, Liquidationen und realisierte PnL bleiben Primaerdaten, die Bitget liefern muss.",
        "Oeffentliche Marktdaten wurden gesichert, aber sie duerfen nur zur Preis-/Zeitpunkt-Plausibilisierung genutzt werden.",
        "",
        "## Betroffene Daten im Bestand",
        "",
        f"- Bitget-Events: `{summary['event_count']}`",
        f"- Zeitraum: `{summary['first_event_utc']}` bis `{summary['last_event_utc']}`",
        f"- Jahre: `{json.dumps(summary['by_year'], ensure_ascii=False)}`",
        f"- Assets: `{format_counts(summary['assets'][:10])}`",
        f"- Symbole: `{format_counts(summary['symbols'][:10])}`",
        "",
        "## Gesicherte externe Public-Market-Daten",
        "",
        f"- Rohdatenordner: `{audit['raw_dir']}`",
        f"- Fetch-Zeitraum: `{fetch['start_date']}` bis `{fetch['end_date']}`",
        "",
        "| Symbol | Spot Rows | Futures Rows | Funding Rows | Aussagekraft |",
        "|---|---:|---:|---:|---|",
    ]
    for symbol, row in fetch["symbols"].items():
        spot = row["spot_history_candles"]
        futures = row["futures_history_candles"]
        funding = row["futures_funding_rates"]
        lines.append(
            f"| `{symbol}` | {spot['row_count']} | {futures['row_count']} | {funding['row_count']} | Preis-/Funding-Plausibilitaet, keine persoenlichen Fills |"
        )
    onchain = audit.get("onchain_transfer_evidence") or {}
    lines += ["", "## Gesicherte On-Chain-Transferbelege", ""]
    lines.append(f"- Gefundene/fetchbare Solana-Signaturen aus Bitget-Events: `{onchain.get('signature_count', 0)}`")
    lines += ["", "| Signatur | Asset | Bitget-Zeit | Status | Chain-Zeit | Aussagekraft |", "|---|---|---|---|---|---|"]
    for signature, record in (onchain.get("records") or {}).items():
        meta = record.get("event_meta") or {}
        chain_summary = record.get("summary") or {}
        lines.append(
            f"| `{signature[:10]}...{signature[-8:]}` | `{meta.get('asset')}` | `{meta.get('event_timestamp_utc')}` | "
            f"`{record.get('status')}` | `{chain_summary.get('block_time_utc', '')}` | externer Transferbeleg, kein Bot-Fill |"
        )
    lines += ["", "## Quellenbewertung", ""]
    for item in audit["source_assessment"]:
        lines.append(f"### {item['source']}")
        lines.append(f"- Status: `{item['status']}`")
        lines.append(f"- Prioritaet: `{item['priority']}`")
        lines.append(f"- Kann belegen: {', '.join(item['can_prove']) or '-'}")
        lines.append(f"- Kann nicht belegen: {', '.join(item['cannot_prove']) or '-'}")
        lines.append(f"- URL: {item['url']}")
        lines.append("")
    lines += [
        "## Schlussfolgerung",
        "",
        "Fuer einen belastbaren Steuerreport ist Bitget selbst die Primaerquelle.",
        "Falls Bitget alte Bot-Details nicht mehr liefert, ist der naechstbeste Weg ein Rekonstruktionsbericht aus:",
        "",
        "- verifizierten externen Ein-/Auszahlungen,",
        "- vorhandenen Bitget-Tax-/Derivate-/Account-Bill-Events,",
        "- Salden vor/nach Bot-Phasen,",
        "- Funding, Fees, Liquidation und realisierter PnL, soweit belegt,",
        "- Public-Market-Candles nur als Preisrahmen.",
        "",
        "Die Public-Market-Daten duerfen nicht genutzt werden, um fehlende einzelne Bot-Trades zu erfinden.",
        "",
    ]
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def top(counter: Counter[str], limit: int) -> list[dict[str, Any]]:
    return [{"key": key, "count": int(count)} for key, count in counter.most_common(limit)]


def format_counts(rows: list[dict[str, Any]]) -> str:
    return ", ".join(f"{row['key']}:{row['count']}" for row in rows)


def date_from_ts(ts: str) -> str:
    if len(ts) >= 10:
        return ts[:10]
    return datetime.now(UTC).date().isoformat()


def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


if __name__ == "__main__":
    main()
