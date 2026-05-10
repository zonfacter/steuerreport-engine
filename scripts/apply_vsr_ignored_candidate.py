#!/usr/bin/env python3
"""Mark reviewed VSR dust/drop artifact as ignored for balance valuation."""

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
REPORT_JSON = ROOT / "var" / "vsr_ignored_candidate_2026-05-09.json"
REPORT_MD = ROOT / "docs" / "122_VSR_IGNORED_CANDIDATE_2026-05-09.md"

TOKEN = {
    "mint": "VSR",
    "reason": (
        "Blockpit/Solana single-unit drop artifact: only withdrawals and later manual "
        "auto-balancing entries, no primary source with material taxable value."
    ),
    "evidence": "Transient audit 2026-05-09: first undercoverage 2024-04-25, worst -1 VSR.",
}


def main() -> None:
    ignored = load_ignored()
    now = datetime.now(UTC).isoformat()
    mint = _normalize_mint(TOKEN["mint"])
    entry = {"reason": TOKEN["reason"], "updated_at_utc": now}
    changed = ignored.get(mint) != entry
    ignored[mint] = entry
    put_admin_setting(SETTING_KEY, ignored, is_secret=False)

    audit = {
        "created_at_utc": now,
        "setting_key": SETTING_KEY,
        "token": TOKEN,
        "inserted_or_updated": 1 if changed else 0,
        "unchanged": 0 if changed else 1,
        "interpretation": [
            "The token remains in raw evidence; only valuation and balance-audit paths that honor runtime.ignored_tokens exclude it.",
            "This is not a deletion and can be reversed if primary evidence for a taxable VSR position appears.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_doc(audit), encoding="utf-8")
    print(
        json.dumps(
            {
                "json": str(REPORT_JSON),
                "doc": str(REPORT_MD),
                "inserted_or_updated": audit["inserted_or_updated"],
                "unchanged": audit["unchanged"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


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
    token = audit["token"]
    lines = [
        "# VSR Ignored Candidate - 2026-05-09",
        "",
        "## Zweck",
        "",
        "VSR als geprueftes Drop-/Dust-Artefakt aus Portfolio- und Balancebewertungen ausblenden, ohne RAW-Belege zu loeschen.",
        "",
        f"- Eingetragen/aktualisiert: `{audit['inserted_or_updated']}`",
        f"- Unveraendert: `{audit['unchanged']}`",
        "",
        "## Evidence",
        "",
        f"- Token: `{token['mint']}`",
        f"- Grund: {token['reason']}",
        f"- Beleg: `{token['evidence']}`",
        "",
        "## Bewertung",
        "",
    ]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
