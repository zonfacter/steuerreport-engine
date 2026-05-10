#!/usr/bin/env python3
"""Mark reviewed obvious spam tokens as ignored for dashboard/audit valuation."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import put_admin_setting
from tax_engine.api.dashboard import _normalize_mint
from tax_engine.ingestion.store import STORE

SETTING_KEY = "runtime.ignored_tokens"
REPORT_JSON = ROOT / "var" / "spam_token_ignored_candidates_2026-05-09.json"
REPORT_MD = ROOT / "docs" / "110_SPAM_TOKEN_IGNORED_CANDIDATES_2026-05-09.md"

IGNORED_TOKENS = [
    {
        "mint": "CM8VSESV7MBHAFD5UDXH84QFGXMAVWJCVVHOPB1DZIF4",
        "reason": "Solana spam mint: unsolicited 1,000,000,000 token mint with promotional whitelist memo; raw evidence retained.",
        "evidence": "tx 5wjYFMr8L1q8vDao9YAk9ScWkdzPwcdkYdQnCMpqSVmRaDnHFrQG5KdwRk6XLgZGfXtvvb7MgEfyTNURrYqv7KzQ",
    },
    {
        "mint": "BONKBOX",
        "reason": "Blockpit manual auto-balancing spam token without transaction id or primary evidence; excluded from portfolio valuation.",
        "evidence": "blockpit-486:in, 2025-07-06, 1,000,000,000 BONKBOX",
    },
    {
        "mint": "JUPDROP",
        "reason": "Repeated Solana drop/spam-style token entries and manual auto-balancing; excluded from portfolio valuation pending contrary primary evidence.",
        "evidence": "Blockpit JUPDROP deposits/auto-balancing 2024-2025",
    },
]


def main() -> None:
    ignored = load_ignored()
    now = datetime.now(UTC).isoformat()
    inserted = 0
    unchanged = 0
    for item in IGNORED_TOKENS:
        mint = _normalize_mint(item["mint"])
        entry = {"reason": item["reason"], "updated_at_utc": now}
        if ignored.get(mint) == entry:
            unchanged += 1
            continue
        ignored[mint] = entry
        inserted += 1
    put_admin_setting(SETTING_KEY, ignored, is_secret=False)
    audit = {
        "created_at_utc": now,
        "setting_key": SETTING_KEY,
        "inserted_or_updated": inserted,
        "unchanged": unchanged,
        "ignored_tokens": IGNORED_TOKENS,
        "interpretation": [
            "Ignored tokens remain in RAW evidence but are excluded from dashboard/portfolio/audit valuation paths that honor runtime.ignored_tokens.",
            "This run only marks obvious spam/drop artifacts; real or traded assets such as PYTH, JUP, SHARK, IOT, SOL and BTC are not ignored.",
            "If contrary primary evidence is found, remove the token from runtime.ignored_tokens instead of deleting RAW rows.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(REPORT_JSON), "doc": str(REPORT_MD), "inserted_or_updated": inserted, "unchanged": unchanged}, ensure_ascii=False, indent=2))


def load_ignored() -> dict[str, dict[str, Any]]:
    row = STORE.get_setting(SETTING_KEY)
    if row is None:
        return {}
    try:
        raw = json.loads(str(row.get("value_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items() if isinstance(value, dict)}


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Spam Token Ignored Candidates - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Offensichtliche Spam-/Drop-Artefakte aus Portfolio- und Bewertungsansichten ausblenden, ohne RAW-Belege zu löschen.",
        "",
        f"- Eingetragen/aktualisiert: `{audit['inserted_or_updated']}`",
        f"- Unveraendert: `{audit['unchanged']}`",
        "",
        "## Ignored Tokens",
        "",
    ]
    for item in audit["ignored_tokens"]:
        lines.append(f"- `{item['mint']}`: {item['reason']} Evidence: `{item['evidence']}`")
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
