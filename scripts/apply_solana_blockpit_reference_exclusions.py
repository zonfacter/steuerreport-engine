#!/usr/bin/env python3
"""Exclude exact Blockpit Solana reference events when Solana RPC primary events exist."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import put_admin_setting
from tax_engine.api.dashboard import (
    _load_token_aliases,
    _normalize_mint,
    _payload_asset_canonical_symbol,
)
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

CREATED_DATE = "2026-05-09"
SETTING_OVERRIDES = "runtime.tax_event_overrides"
SETTING_ALIASES = "runtime.token_aliases"
REPORT_JSON = ROOT / "var" / f"solana_blockpit_reference_exclusions_{CREATED_DATE}.json"
REPORT_MD = ROOT / "docs" / f"112_SOLANA_BLOCKPIT_REFERENCE_EXCLUSIONS_{CREATED_DATE}.md"
REASON_CODE = "reference_import_only"
REASON_LABEL = "Nur Referenzimport, Primärdaten sind bereits vorhanden"

ALIAS_UPSERTS = {
    "7ATGF8KQO4WJRD5ATGX7T1V2ZVVYKPJBFFNEVF1ICFV1": {
        "symbol": "CWIF",
        "name": "catwifhat",
        "notes": "Inferred from exact Blockpit/Solana tx matches; used for duplicate reference exclusion.",
    },
    "2KFZCKFXJ1US8YRQZA5VKTSXY3GPZFZVVHWJ91N8FV2J": {
        "symbol": "CBDC",
        "name": "CBDC",
        "notes": "Inferred from exact Blockpit/Solana tx matches; used for duplicate reference exclusion.",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    aliases = _load_token_aliases()
    aliases_with_pending = dict(aliases)
    aliases_with_pending.update(ALIAS_UPSERTS)
    matches = find_exact_matches(aliases_with_pending)
    now = datetime.now(UTC).isoformat()
    import_result = None
    if args.execute:
        overrides = load_setting_dict(SETTING_OVERRIDES)
        inserted = 0
        unchanged = 0
        for item in matches:
            event_id = item["blockpit_event_id"]
            entry = {
                "tax_category": "EXCLUDED",
                "reason_code": REASON_CODE,
                "reason_label": REASON_LABEL,
                "note": (
                    "Blockpit Solana reference event excluded because an exact Solana RPC primary event exists "
                    f"for tx {item['tx_id']} / asset {item['asset']} / quantity {item['quantity']}."
                ),
                "updated_at_utc": now,
            }
            if overrides.get(event_id) == entry:
                unchanged += 1
                continue
            overrides[event_id] = entry
            inserted += 1
        stored_aliases = load_setting_dict(SETTING_ALIASES)
        alias_inserted = 0
        for mint, payload in ALIAS_UPSERTS.items():
            if stored_aliases.get(mint) == payload:
                continue
            stored_aliases[mint] = payload
            alias_inserted += 1
        put_admin_setting(SETTING_OVERRIDES, overrides, is_secret=False)
        put_admin_setting(SETTING_ALIASES, stored_aliases, is_secret=False)
        import_result = {
            "excluded_event_count": inserted,
            "unchanged_exclusions": unchanged,
            "alias_inserted_or_updated": alias_inserted,
        }

    audit = {
        "created_at_utc": now,
        "mode": "execute" if args.execute else "preview",
        "match_count": len(matches),
        "matches": matches[:500],
        "alias_upserts": ALIAS_UPSERTS,
        "import_result": import_result,
        "interpretation": [
            "Only exact matches are used: tx_id, canonical asset, side, quantity and timestamp must align.",
            "Solana RPC is treated as primary on-chain evidence; Blockpit Solana rows are retained as RAW evidence but excluded tax-effectively.",
            "Alias upserts are limited to mints that match Blockpit symbols on the same Solana transaction and amount.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "mode": audit["mode"], "match_count": len(matches), "import_result": import_result}, ensure_ascii=False, indent=2))


def find_exact_matches(aliases: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    raw, _ = apply_review_actions(STORE.list_raw_events())
    events, _ = apply_tax_event_overrides(raw)
    primary: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    references: list[dict[str, Any]] = []
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if not payload:
            continue
        source = str(payload.get("source") or "").lower().strip()
        tx_id = event_tx_id(payload)
        if not tx_id:
            continue
        asset = _payload_asset_canonical_symbol(payload, aliases)
        key = (
            tx_id,
            str(payload.get("timestamp_utc") or payload.get("timestamp") or ""),
            asset,
            str(payload.get("side") or "").lower().strip(),
            plain(dec(payload.get("quantity"))),
        )
        item = {
            "event_id": str(event.get("unique_event_id") or ""),
            "source": source,
            "tx_id": tx_id,
            "timestamp_utc": key[1],
            "asset": asset,
            "side": key[3],
            "quantity": key[4],
            "event_type": str(payload.get("event_type") or ""),
        }
        if source == "solana_rpc":
            primary[key].append(item)
        elif source == "blockpit" and is_blockpit_solana_reference(payload):
            references.append(item)
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ref in references:
        key = (ref["tx_id"], ref["timestamp_utc"], ref["asset"], ref["side"], ref["quantity"])
        primary_rows = primary.get(key, [])
        if not primary_rows or ref["event_id"] in seen:
            continue
        seen.add(ref["event_id"])
        matches.append(
            {
                "blockpit_event_id": ref["event_id"],
                "solana_rpc_event_id": primary_rows[0]["event_id"],
                "tx_id": ref["tx_id"],
                "timestamp_utc": ref["timestamp_utc"],
                "asset": ref["asset"],
                "side": ref["side"],
                "quantity": ref["quantity"],
                "blockpit_event_type": ref["event_type"],
                "solana_rpc_event_type": primary_rows[0]["event_type"],
            }
        )
    return sorted(matches, key=lambda item: (item["timestamp_utc"], item["asset"], item["tx_id"]))


def is_blockpit_solana_reference(payload: dict[str, Any]) -> bool:
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    integration = str(raw.get("Integration Name") or raw.get("integration") or "").lower()
    source_type = str(raw.get("Source Type") or "").lower()
    return "solana" in integration and source_type == "chain"


def event_tx_id(payload: dict[str, Any]) -> str:
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    source = str(payload.get("source") or "").lower().strip()
    if source == "blockpit":
        raw_tx = str(raw.get("Trx. ID (optional)") or raw.get("txid") or raw.get("tx_id") or "").strip()
        if raw_tx:
            return raw_tx
    return str(payload.get("tx_id") or "").strip()


def load_setting_dict(key: str) -> dict[str, dict[str, Any]]:
    row = STORE.get_setting(key)
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    return {_normalize_mint(str(k)) if key == SETTING_ALIASES else str(k): v for k, v in raw.items() if isinstance(v, dict)}


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Solana Blockpit Reference Exclusions - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Exakte Blockpit-Solana-Referenzzeilen ausschliessen, wenn dieselbe On-Chain-Bewegung bereits aus Solana-RPC als Primaerdatensatz vorhanden ist.",
        "",
        f"- Modus: `{audit['mode']}`",
        f"- Exact Matches: `{audit['match_count']}`",
        f"- Import Result: `{audit['import_result']}`",
        "",
        "## Alias Upserts",
        "",
    ]
    for mint, payload in audit["alias_upserts"].items():
        lines.append(f"- `{mint}` -> `{payload['symbol']}` ({payload['name']})")
    lines += ["", "## Beispiele", ""]
    for item in audit["matches"][:25]:
        lines.append(
            f"- `{item['timestamp_utc']}` `{item['asset']}` `{item['quantity']}` `{item['side']}` "
            f"tx `{item['tx_id']}` blockpit `{item['blockpit_event_id']}` rpc `{item['solana_rpc_event_id']}`"
        )
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    return "\n".join(lines) + "\n"


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Decimal) -> str:
    return value.normalize().to_eng_string() if value else "0"


if __name__ == "__main__":
    main()
