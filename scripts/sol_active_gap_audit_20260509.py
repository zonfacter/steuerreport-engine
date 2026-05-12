#!/usr/bin/env python3
"""Summarize the current active SOL balance gap."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BALANCE_JSON = ROOT / "var" / "chronological_balance_break_audit_after_binance_sol_reconstruction_2026-05-09.json"
TRANSIENT_JSON = ROOT / "var" / "transient_balance_undercoverage_audit_2026-05-09.json"
PLATFORM_SIM_JSON = ROOT / "var" / "platform_balance_simulation_2026-05-09.json"
TRANSFER_GROUPS_JSON = ROOT / "var" / "platform_transfer_groups_2026-05-09.json"
CANDIDATES_JSON = ROOT / "var" / "platform_transfer_candidates_2026-05-09.json"
OUTPUT_JSON = ROOT / "var" / "sol_active_gap_audit_2026-05-09.json"
OUTPUT_DOC = ROOT / "docs" / "148_SOL_ACTIVE_GAP_AUDIT_2026-05-09.md"


def main() -> None:
    balance = read_json(BALANCE_JSON)
    transient = read_json(TRANSIENT_JSON)
    platform = read_json(PLATFORM_SIM_JSON)
    groups = read_json(TRANSFER_GROUPS_JSON)
    candidates = read_json(CANDIDATES_JSON)

    global_sol = select_asset(balance.get("asset_reports") or [], "SOL")
    transient_sol = select_asset(transient.get("asset_reports") or [], "SOL")
    platform_sol = [row for row in platform.get("negative_assets") or [] if row.get("asset") == "SOL"]
    sol_groups = [row for row in groups.get("groups") or [] if row.get("asset") == "SOL"]
    break_links = [
        row
        for row in candidates.get("negative_break_links") or []
        if row.get("asset") == "SOL" and row.get("platform") == "binance"
    ]
    matched_binance_to_wallet = [
        slim_group(row)
        for row in sol_groups
        if has_platform(row, "binance") and has_platform(row, "solana_wallet")
    ]
    sol_final = str((global_sol or {}).get("final_balance") or "")
    sol_has_break = bool((global_sol or {}).get("first_negative"))
    assessment = [
        "Die sichtbaren Binance-SOL-Withdrawals sind per gleicher TXID mit Solana-Wallet-Inflows gematcht.",
    ]
    if sol_final.startswith("-") or sol_has_break:
        assessment.extend(
            [
                "Das Restproblem ist nicht die Wallet-Gegenbuchung, sondern fehlender aktiver Binance-SOL-Bestand vor den Withdrawals.",
                "Naechstes Evidence-Ziel: Binance SOL-Kaeufe, Convert, Earn/Staking-Redemption oder Blockpit-Referenzzeilen vor 2023-05-08, die sicher als aktive Primaerrekonstruktion taugen.",
            ]
        )
    else:
        assessment.extend(
            [
                "Nach der Binance-SOL-2023-Rekonstruktion zeigt SOL keinen aktiven Negativbestand mehr.",
                "Der Gegenwert der SOL-Kaeufe wurde korrekt als BTC-Abgang gebucht; dadurch ist jetzt BTC die naechste aktive Quellenluecke.",
            ]
        )
    payload = {
        "global_active_sol": slim_asset(global_sol),
        "transient_active_sol": slim_asset(transient_sol),
        "platform_negative_sol": platform_sol,
        "binance_sol_break_links": break_links,
        "matched_binance_to_wallet_transfer_count": len(matched_binance_to_wallet),
        "matched_binance_to_wallet_transfers": matched_binance_to_wallet,
        "assessment": assessment,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_DOC.write_text(render_doc(payload), encoding="utf-8")
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(OUTPUT_DOC), "matched_transfers": len(matched_binance_to_wallet)}, ensure_ascii=False, indent=2))


def read_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def select_asset(rows: list[dict[str, Any]], asset: str) -> dict[str, Any]:
    for row in rows:
        if row.get("asset") == asset:
            return row
    return {}


def slim_asset(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset": row.get("asset"),
        "final_balance": row.get("final_balance"),
        "event_count": row.get("event_count"),
        "first_negative": row.get("first_negative"),
        "worst_balance": row.get("worst_balance"),
        "yearly_net": row.get("yearly_net"),
        "source_net_top": (row.get("source_net_top") or [])[:12],
    }


def has_platform(group: dict[str, Any], platform: str) -> bool:
    return any((row.get("platform") == platform) for row in group.get("rows") or [])


def slim_group(group: dict[str, Any]) -> dict[str, Any]:
    return {
        "tx_id": group.get("tx_id"),
        "rows": [
            {
                "ledger_id": row.get("ledger_id"),
                "normalized_timestamp_utc": row.get("normalized_timestamp_utc"),
                "platform": row.get("platform"),
                "quantity_delta": row.get("quantity_delta"),
                "event_type": row.get("event_type"),
                "source": row.get("source"),
                "counterparty_address": row.get("counterparty_address"),
            }
            for row in group.get("rows") or []
        ],
    }


def render_doc(payload: dict[str, Any]) -> str:
    global_sol = payload["global_active_sol"]
    first = global_sol.get("first_negative") or {}
    worst = global_sol.get("worst_balance") or {}
    lines = [
        "# SOL Active Gap Audit - 2026-05-09",
        "",
        "## Ergebnis",
        "",
        f"- Aktiver globaler SOL-Endsaldo: `{global_sol.get('final_balance')}`",
        f"- Erster SOL-Bruch: `{first.get('timestamp')}` `{first.get('source')}` `{first.get('event_type')}` delta `{first.get('delta')}` after `{first.get('balance_after')}` tx `{first.get('tx_id')}`",
        f"- Schlimmster SOL-Stand: `{worst.get('balance_after')}` am `{worst.get('timestamp')}`",
        f"- Gematchte Binance -> Solana-Wallet SOL-Transfers: `{payload['matched_binance_to_wallet_transfer_count']}`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["assessment"])
    lines += [
        "",
        "## Plattform-Breaks",
        "",
    ]
    for row in payload["platform_negative_sol"]:
        first = row.get("first_negative") or {}
        lines.append(
            f"- `{row.get('platform')}` final `{row.get('final_balance')}` worst `{row.get('worst_balance')}` "
            f"first `{first.get('normalized_timestamp_utc')}` tx `{first.get('tx_id')}`"
        )
    lines += [
        "",
        "## Gematchte Binance-Solana-Transfers",
        "",
    ]
    for group in payload["matched_binance_to_wallet_transfers"][:20]:
        lines.append(f"- TX `{group.get('tx_id')}`")
        for row in group["rows"]:
            lines.append(
                f"  - `{row['normalized_timestamp_utc']}` `{row['platform']}` `{row['quantity_delta']}` `{row['event_type']}` `{row['source']}`"
            )
    lines += [
        "",
        "## Naechster Schritt",
        "",
        "- Falls SOL positiv bleibt: BTC-Deckung der rekonstruierten SOL-Kaeufe kontrolliert weiterverfolgen.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
