from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from tax_engine.connectors.token_metadata import resolve_token_metadata
from tax_engine.ingestion.store import STORE

DEX_PROGRAMS = {
    "jupiter",
    "phoenix_v1",
    "whirlpool",
    "lifinity_amm_v2",
    "amm_v3",
    "raydium_amm",
    "openbook_v2",
    "SaberStableSwap",
    "lb_clmm",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic preview for missing Solscan wallet events.")
    parser.add_argument("--wallet-address", required=True)
    parser.add_argument("--json-out", default="")
    parser.add_argument("--md-out", default="")
    args = parser.parse_args()

    wallet = args.wallet_address.strip()
    preview = build_preview(wallet)

    json_out = Path(args.json_out or f"var/solscan_missing_event_preview_{wallet[:6]}_2026-05-08.json")
    md_out = Path(args.md_out or f"docs/42_SOLSCAN_MISSING_EVENT_PREVIEW_{wallet[:6]}_2026-05-08.md")
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(_render_markdown(preview, json_out=json_out), encoding="utf-8")
    print(
        json.dumps(
            {
                "wallet_address": wallet,
                "missing_signatures": preview["summary"]["missing_signatures"],
                "proposed_rows": preview["summary"]["proposed_rows"],
                "class_counts": preview["summary"]["class_counts"],
                "json_out": str(json_out),
                "md_out": str(md_out),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def build_preview(wallet: str) -> dict[str, Any]:
    # Older Solana imports did not always persist wallet_address in every derived row.
    # Signature-level duplicate detection must therefore compare against all solana_rpc tx ids.
    known = set(STORE.list_distinct_transaction_ids(source="solana_rpc", limit=1000000))
    with STORE._connect() as conn:
        tx_rows = conn.execute(
            """
            SELECT signature, block_time_utc, status, raw_json
            FROM solscan_account_transactions
            WHERE wallet_address = ?
            ORDER BY block_time_utc ASC, signature ASC
            """,
            (wallet,),
        ).fetchall()
        transfer_rows = conn.execute(
            """
            SELECT signature, flow, activity_type, token_address, token_decimals, amount, value_usd,
                   block_time_utc, from_address, to_address, raw_json
            FROM solscan_account_transfers
            WHERE wallet_address = ?
            ORDER BY block_time_utc ASC, signature ASC
            """,
            (wallet,),
        ).fetchall()

    transfers_by_sig: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in transfer_rows:
        transfers_by_sig[str(row["signature"])].append(dict(row))

    signatures: list[dict[str, Any]] = []
    proposed_rows: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    year_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for row in tx_rows:
        signature = str(row["signature"])
        if signature in known:
            continue
        raw = json.loads(str(row["raw_json"]))
        programs = _programs(raw)
        transfers = transfers_by_sig.get(signature, [])
        classification = _classify(programs=programs, transfers=transfers)
        class_counts[classification] += 1
        year_counts[str(row["block_time_utc"])[:4]][classification] += 1
        rows_for_signature = _rows_for_signature(
            wallet=wallet,
            signature=signature,
            timestamp_utc=str(row["block_time_utc"]),
            classification=classification,
            programs=programs,
            transfers=transfers,
        )
        proposed_rows.extend(rows_for_signature)
        signatures.append(
            {
                "signature": signature,
                "timestamp_utc": str(row["block_time_utc"]),
                "status": str(row["status"]),
                "classification": classification,
                "programs": programs,
                "transfer_count": len(transfers),
                "proposed_row_count": len(rows_for_signature),
            }
        )

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "wallet_address": wallet,
        "summary": {
            "known_imported_solana_rpc": len(known),
            "solscan_account_transactions": len(tx_rows),
            "missing_signatures": len(signatures),
            "proposed_rows": len(proposed_rows),
            "class_counts": dict(class_counts),
            "year_class_counts": {year: dict(counts) for year, counts in sorted(year_counts.items())},
        },
        "signatures": signatures,
        "proposed_rows": proposed_rows,
    }


def _rows_for_signature(
    *,
    wallet: str,
    signature: str,
    timestamp_utc: str,
    classification: str,
    programs: list[str],
    transfers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if classification == "technical_account_or_metadata":
        return []

    net_by_token: dict[str, Decimal] = defaultdict(Decimal)
    value_by_token: dict[str, Decimal] = defaultdict(Decimal)
    decimals_by_token: dict[str, int | None] = {}
    raw_transfers: list[dict[str, Any]] = []
    for transfer in transfers:
        token = str(transfer.get("token_address") or "").strip()
        if not token:
            continue
        amount = _ui_amount(transfer.get("amount"), transfer.get("token_decimals"))
        if amount == 0:
            continue
        sign = Decimal("1") if str(transfer.get("flow") or "").lower() == "in" else Decimal("-1")
        net_by_token[token] += sign * amount
        decimals_by_token[token] = _int_or_none(transfer.get("token_decimals"))
        value_by_token[token] += _decimal_or_zero(transfer.get("value_usd"))
        raw_transfers.append({key: transfer.get(key) for key in ("flow", "activity_type", "token_address", "token_decimals", "amount", "value_usd", "from_address", "to_address")})

    rows: list[dict[str, Any]] = []
    for token, net_amount in sorted(net_by_token.items(), key=lambda item: resolve_token_metadata(item[0])["symbol"]):
        if net_amount == 0:
            continue
        meta = resolve_token_metadata(token)
        side = "in" if net_amount > 0 else "out"
        event_type = _event_type_for(classification=classification, side=side, token=token)
        rows.append(
            {
                "timestamp_utc": timestamp_utc,
                "wallet_address": wallet,
                "asset": meta["symbol"],
                "asset_address": token,
                "quantity": abs(net_amount).normalize().to_eng_string(),
                "price": "",
                "fee": "0",
                "fee_asset": "",
                "side": side,
                "event_type": event_type,
                "defi_label": "swap" if classification == "dex_swap_or_route" else "transfer",
                "tx_id": signature,
                "source": "solscan_wallet_discovery",
                "raw_row": {
                    "solscan_signature": signature,
                    "classification": classification,
                    "programs": programs,
                    "token_address": token,
                    "token_decimals": decimals_by_token.get(token),
                    "net_amount": net_amount.normalize().to_eng_string(),
                    "value_usd_sum": value_by_token[token].normalize().to_eng_string(),
                    "raw_transfer_count": len(raw_transfers),
                    "raw_transfers": raw_transfers,
                },
            }
        )
    return rows


def _event_type_for(*, classification: str, side: str, token: str) -> str:
    symbol = resolve_token_metadata(token)["symbol"]
    if classification == "dex_swap_or_route":
        return "swap_in_aggregated" if side == "in" else "swap_out_aggregated"
    return "sol_transfer" if symbol == "SOL" else "token_transfer"


def _classify(*, programs: list[str], transfers: list[dict[str, Any]]) -> str:
    nonzero = [transfer for transfer in transfers if _ui_amount(transfer.get("amount"), transfer.get("token_decimals")) != 0]
    flows = {str(transfer.get("flow") or "").lower() for transfer in nonzero}
    if "jupiter" in programs or any(program in DEX_PROGRAMS for program in programs):
        return "dex_swap_or_route"
    if nonzero and flows <= {"in"}:
        return "transfer_in_or_airdrop"
    if nonzero and flows <= {"out"}:
        return "transfer_out"
    if nonzero:
        return "mixed_transfer"
    if set(programs) <= {"system", "spl-token", "ComputeBudget", "mpl_token_metadata"}:
        return "technical_account_or_metadata"
    return "unknown_needs_detail"


def _programs(raw: dict[str, Any]) -> list[str]:
    programs: list[str] = []
    for item in raw.get("parsed_instructions") or []:
        if not isinstance(item, dict):
            continue
        program = str(item.get("program") or item.get("program_id") or "").strip()
        if program:
            programs.append(program)
    return programs


def _ui_amount(raw_amount: Any, raw_decimals: Any) -> Decimal:
    amount = _decimal_or_zero(raw_amount)
    decimals = _int_or_none(raw_decimals) or 0
    if decimals <= 0:
        return amount
    return amount / (Decimal(10) ** decimals)


def _decimal_or_zero(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except InvalidOperation:
        return Decimal("0")


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _render_markdown(preview: dict[str, Any], *, json_out: Path) -> str:
    summary = preview["summary"]
    lines = [
        "# Solscan Missing Event Preview 2026-05-08",
        "",
        f"- Wallet: `{preview['wallet_address']}`",
        f"- Bekannte lokale Solana-RPC-Signaturen: `{summary['known_imported_solana_rpc']}`",
        f"- Solscan Account-Transactions: `{summary['solscan_account_transactions']}`",
        f"- Fehlende Signaturen: `{summary['missing_signatures']}`",
        f"- Vorgeschlagene Event-Zeilen: `{summary['proposed_rows']}`",
        f"- JSON: `{json_out}`",
        "",
        "## Klassen",
    ]
    for name, count in sorted(summary["class_counts"].items()):
        lines.append(f"- `{name}`: `{count}`")
    lines.append("")
    lines.append("## Jahr/Klasse")
    for year, counts in summary["year_class_counts"].items():
        parts = ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
        lines.append(f"- `{year}`: {parts}")
    lines.append("")
    lines.append("## Bewertung")
    lines.append("- Diese Datei ist ein Preview, noch kein Import.")
    lines.append("- `dex_swap_or_route` wird als Netto-Bewegung je Token vorgeschlagen; komplexe Routen koennen mehrere In-/Out-Zeilen erzeugen.")
    lines.append("- `technical_account_or_metadata` erzeugt keine steuerliche Event-Zeile.")
    lines.append("- Vor dem produktiven Import sollte die Auswirkung auf negative Bestände per Dry-Run geprüft werden.")
    lines.append("")
    lines.append("## Erste vorgeschlagene Zeilen")
    for row in preview["proposed_rows"][:30]:
        lines.append(
            f"- `{row['timestamp_utc']}` `{row['event_type']}` `{row['side']}` "
            f"`{row['quantity']} {row['asset']}` tx=`{row['tx_id']}`"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
