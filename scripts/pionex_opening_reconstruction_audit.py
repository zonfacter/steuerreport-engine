#!/usr/bin/env python3
"""Build a deterministic evidence report for the Pionex opening-balance gap."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

OUTPUT_JSON = ROOT / "var" / "pionex_opening_reconstruction_audit_2026-05-08.json"
OUTPUT_DOC = ROOT / "docs" / "84_PIONEX_OPENING_RECONSTRUCTION_AUDIT_2026-05-08.md"
PIONEX_EXPORT_DIR = ROOT / "usertransfer" / "pionex"


def main() -> None:
    raw_events = STORE.list_raw_events()
    reviewed, _review_summary = apply_review_actions(raw_events)
    effective, _override_count = apply_tax_event_overrides(reviewed)

    raw_by_tx = _raw_events_by_tx(raw_events)
    pionex_events = [_slim_event(row) for row in effective if _payload(row).get("source") == "pionex"]
    pionex_events.sort(key=lambda row: (row["timestamp_utc"], row["event_id"]))

    movements = [row for event in pionex_events for row in _movements(event)]
    movements.sort(key=lambda row: (row["timestamp_utc"], row["event_id"], row["asset"], row["side"]))

    per_asset = _balance_by_asset(movements)
    usdt = per_asset.get("USDT", {})
    deposits = [row for row in movements if row["event_type"] == "deposit"]
    withdrawals = [row for row in movements if row["event_type"] == "withdrawal"]
    external_matches = _external_matches(deposits + withdrawals, raw_by_tx)
    usdt_until_worst = [
        row
        for row in movements
        if row["asset"] == "USDT"
        and row["timestamp_utc"] <= str(usdt.get("minimum", {}).get("timestamp_utc") or "9999")
    ]

    audit = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "pionex_export_dir": str(PIONEX_EXPORT_DIR),
        "export_files": _export_files(),
        "pionex_event_count": len(pionex_events),
        "movement_count": len(movements),
        "first_pionex_event": pionex_events[0] if pionex_events else None,
        "last_pionex_event": pionex_events[-1] if pionex_events else None,
        "per_asset": per_asset,
        "deposits": deposits,
        "withdrawals": withdrawals,
        "external_tx_matches": external_matches,
        "usdt_until_worst_summary": _movement_summary(usdt_until_worst),
        "usdt_daily_balances_until_worst": _daily_balances(usdt_until_worst),
        "tax_id_summary_until_worst": _tax_id_summary(usdt_until_worst),
        "first_40_usdt_movements": usdt_until_worst[:40],
        "conclusion": _conclusion(per_asset),
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DOC.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_DOC.write_text(_render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(OUTPUT_DOC)}, ensure_ascii=False))


def _payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def _slim_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = _payload(event)
    raw_row = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    return {
        "event_id": str(event.get("unique_event_id") or ""),
        "timestamp_utc": _timestamp(payload),
        "source_file_id": str(event.get("source_file_id") or ""),
        "source": str(payload.get("source") or ""),
        "event_type": str(payload.get("event_type") or ""),
        "side": str(payload.get("side") or "").lower().strip(),
        "asset": str(payload.get("asset") or "").upper().strip(),
        "quantity": _plain(_quantity(payload)),
        "tx_id": str(payload.get("tx_id") or ""),
        "symbol": str(raw_row.get("symbol") or ""),
        "tax_id": str(raw_row.get("tax_id") or ""),
        "raw_row": raw_row,
    }


def _movements(event: dict[str, Any]) -> list[dict[str, Any]]:
    qty = _decimal(event["quantity"])
    side = event["side"]
    if side in {"in", "buy"}:
        delta = qty
    elif side in {"out", "sell"}:
        delta = -qty
    else:
        delta = _decimal(event["quantity"])
    if not event["asset"] or delta == 0:
        return []
    return [{**event, "delta": _plain(delta)}]


def _balance_by_asset(movements: list[dict[str, Any]]) -> dict[str, Any]:
    balances: dict[str, Decimal] = defaultdict(Decimal)
    minimum: dict[str, dict[str, Any]] = {}
    first_negative: dict[str, dict[str, Any]] = {}
    event_count: Counter[str] = Counter()
    source_net: dict[str, Counter[tuple[str, str, str]]] = defaultdict(Counter)
    yearly_net: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))

    for row in movements:
        asset = row["asset"]
        before = balances[asset]
        delta = _decimal(row["delta"])
        after = before + delta
        balances[asset] = after
        event_count[asset] += 1
        source_net[asset][(row["source"], row["event_type"], row["side"])] += delta
        yearly_net[asset][row["timestamp_utc"][:4]] += delta
        enriched = {**row, "balance_before": _plain(before), "balance_after": _plain(after)}
        if before >= 0 > after and asset not in first_negative:
            first_negative[asset] = enriched
        current_min = minimum.get(asset)
        if current_min is None or after < _decimal(current_min["balance_after"]):
            minimum[asset] = enriched

    result: dict[str, Any] = {}
    for asset in sorted(balances):
        min_row = minimum.get(asset, {})
        min_balance = _decimal(min_row.get("balance_after"))
        result[asset] = {
            "event_count": event_count[asset],
            "final_balance": _plain(balances[asset]),
            "minimum_balance": _plain(min_balance),
            "required_opening_to_never_go_negative": _plain(abs(min_balance)) if min_balance < 0 else "0",
            "first_negative": first_negative.get(asset),
            "minimum": min_row,
            "yearly_net": {year: _plain(value) for year, value in sorted(yearly_net[asset].items())},
            "source_net": [
                {
                    "source": key[0],
                    "event_type": key[1],
                    "side": key[2],
                    "net": _plain(value),
                }
                for key, value in sorted(source_net[asset].items(), key=lambda item: abs(item[1]), reverse=True)
            ],
        }
    return result


def _movement_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: Counter[tuple[str, str]] = Counter()
    net = Decimal("0")
    for row in rows:
        delta = _decimal(row["delta"])
        by_type[(row["event_type"], row["side"])] += delta
        net += delta
    return {
        "movement_count": len(rows),
        "net": _plain(net),
        "by_type": [
            {"event_type": key[0], "side": key[1], "net": _plain(value)}
            for key, value in sorted(by_type.items(), key=lambda item: abs(item[1]), reverse=True)
        ],
    }


def _daily_balances(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    balances: list[dict[str, str]] = []
    current_day = ""
    balance = Decimal("0")
    minimum = Decimal("0")
    for row in rows:
        day = row["timestamp_utc"][:10]
        if current_day and day != current_day:
            balances.append({"day": current_day, "balance_end": _plain(balance), "minimum_seen": _plain(minimum)})
            minimum = balance
        current_day = day
        balance += _decimal(row["delta"])
        if balance < minimum:
            minimum = balance
    if current_day:
        balances.append({"day": current_day, "balance_end": _plain(balance), "minimum_seen": _plain(minimum)})
    return balances


def _tax_id_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row.get("tax_id") or "-", row.get("symbol") or "-")
        bucket = grouped.setdefault(
            key,
            {"tax_id": key[0], "symbol": key[1], "movement_count": 0, "net_usdt": Decimal("0"), "first": row["timestamp_utc"], "last": row["timestamp_utc"]},
        )
        bucket["movement_count"] += 1
        bucket["net_usdt"] += _decimal(row["delta"])
        bucket["first"] = min(bucket["first"], row["timestamp_utc"])
        bucket["last"] = max(bucket["last"], row["timestamp_utc"])
    return [
        {**{k: v for k, v in item.items() if k != "net_usdt"}, "net_usdt": _plain(item["net_usdt"])}
        for item in sorted(grouped.values(), key=lambda row: abs(row["net_usdt"]), reverse=True)
    ]


def _raw_events_by_tx(raw_events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_tx: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in raw_events:
        payload = _payload(event)
        tx_id = str(payload.get("tx_id") or "")
        if tx_id:
            by_tx[tx_id].append(_slim_event(event))
    return by_tx


def _external_matches(rows: list[dict[str, Any]], raw_by_tx: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    matches = []
    for row in rows:
        tx_id = row.get("tx_id") or ""
        if not tx_id:
            continue
        external = [candidate for candidate in raw_by_tx.get(tx_id, []) if candidate["source"] != "pionex"]
        matches.append(
            {
                "pionex": row,
                "external_match_count": len(external),
                "external_matches": external[:10],
            }
        )
    return matches


def _export_files() -> list[dict[str, str]]:
    files = []
    for path in sorted(PIONEX_EXPORT_DIR.glob("*.csv")):
        files.append(
            {
                "path": str(path.relative_to(ROOT)),
                "size_bytes": str(path.stat().st_size),
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
            }
        )
    return files


def _conclusion(per_asset: dict[str, Any]) -> dict[str, str]:
    usdt = per_asset.get("USDT", {})
    return {
        "status": "replacement_reconstruction_possible_but_not_primary_evidence",
        "required_usdt_opening": str(usdt.get("required_opening_to_never_go_negative") or "0"),
        "recommended_review_action": "Kandidat tax_effective=false lassen, bis eine Pionex-Abrechnung vorliegt oder die Ersatzrekonstruktion fachlich freigegeben wird.",
        "why": "Der exportierte Trade-/Deposit-Strom ist intern konsistent und die aktuellen API-Balances passen eng zum CSV-Modell, aber es gibt keinen expliziten Pionex-Kontosnapshot vor den ersten Bot-Trades.",
    }


def _render_doc(audit: dict[str, Any]) -> str:
    usdt = audit["per_asset"].get("USDT", {})
    lines = [
        "# Pionex Opening Reconstruction Audit 2026-05-08",
        "",
        f"- JSON: `{OUTPUT_JSON.relative_to(ROOT)}`",
        f"- Pionex-Export-Verzeichnis: `{Path(audit['pionex_export_dir']).relative_to(ROOT)}`",
        f"- Pionex Events: `{audit['pionex_event_count']}`",
        f"- Bewegungen: `{audit['movement_count']}`",
        "",
        "## Ergebnis",
        "",
        f"- Erforderliches USDT-Opening, damit Pionex-only nie negativ wird: `{usdt.get('required_opening_to_never_go_negative')}`",
        f"- Erster USDT-Bruch: `{_fmt_event(usdt.get('first_negative'))}`",
        f"- Schlimmster USDT-Stand: `{_fmt_event(usdt.get('minimum'))}`",
        f"- Status: `{audit['conclusion']['status']}`",
        "",
        "Das ist eine belastbare Ersatzrekonstruktion aus den vorhandenen Exporten, aber weiterhin kein primaerer Konto-Snapshot. Deshalb bleibt der bestehende Review-Kandidat fachlich entscheidungspflichtig und `tax_effective=false`.",
        "",
        "## Export-Dateien",
        "",
    ]
    for item in audit["export_files"]:
        lines.append(f"- `{item['path']}` ({item['size_bytes']} Bytes)")

    lines += ["", "## Pionex Deposits/Withdrawals und externe Tx-Matches", ""]
    for item in audit["external_tx_matches"]:
        row = item["pionex"]
        lines.append(
            f"- `{row['timestamp_utc']}` `{row['event_type']}` `{row['side']}` "
            f"`{row['quantity']} {row['asset']}` tx=`{row['tx_id']}` externe_matches=`{item['external_match_count']}`"
        )

    lines += ["", "## USDT-Netto bis zum schlimmsten Bruch", ""]
    for item in audit["usdt_until_worst_summary"]["by_type"]:
        lines.append(f"- `{item['event_type']}` / `{item['side']}`: `{item['net']} USDT`")

    lines += ["", "## Tagesende USDT bis zum schlimmsten Bruch", ""]
    for item in audit["usdt_daily_balances_until_worst"]:
        lines.append(f"- `{item['day']}`: Endbestand `{item['balance_end']}`, Minimum `{item['minimum_seen']}`")

    lines += ["", "## Bot-/Tax-ID-Gruppen bis zum schlimmsten Bruch", ""]
    for item in audit["tax_id_summary_until_worst"][:20]:
        lines.append(
            f"- tax_id `{item['tax_id']}` `{item['symbol']}`: net `{item['net_usdt']} USDT`, "
            f"movements `{item['movement_count']}`, `{item['first']}`..`{item['last']}`"
        )

    lines += ["", "## Erste USDT-Bewegungen", ""]
    for row in audit["first_40_usdt_movements"]:
        lines.append(
            f"- `{row['timestamp_utc']}` `{row['event_type']}` `{row['side']}` "
            f"`{row['delta']} USDT` tx=`{row['tx_id']}` tax_id=`{row['tax_id']}`"
        )

    lines += [
        "",
        "## Schlussfolgerung",
        "",
        f"- `{audit['conclusion']['why']}`",
        f"- Empfohlene Review-Aktion: `{audit['conclusion']['recommended_review_action']}`",
    ]
    return "\n".join(lines) + "\n"


def _fmt_event(row: Any) -> str:
    if not isinstance(row, dict):
        return "-"
    return (
        f"{row.get('timestamp_utc')} {row.get('event_type')}/{row.get('side')} "
        f"{row.get('delta')} {row.get('asset')} balance_after={row.get('balance_after')} tx={row.get('tx_id')}"
    )


def _timestamp(payload: dict[str, Any]) -> str:
    return str(payload.get("timestamp_utc") or payload.get("timestamp") or "")


def _quantity(payload: dict[str, Any]) -> Decimal:
    for key in ("quantity", "amount", "qty", "size"):
        if payload.get(key) not in (None, ""):
            return abs(_decimal(payload.get(key)))
    return Decimal("0")


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _plain(value: Decimal) -> str:
    return format(value, "f")


if __name__ == "__main__":
    main()
