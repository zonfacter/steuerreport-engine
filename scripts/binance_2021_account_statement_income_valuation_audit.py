#!/usr/bin/env python3
"""Check valuation coverage for reviewed Binance 2021 account-statement income rows."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from import_binance_2021_account_statement_income import build_rows

from tax_engine.ingestion.store import STORE

CREATED_DATE = "2026-05-09"
JSON_PATH = ROOT / "var" / f"binance_2021_account_statement_income_valuation_audit_{CREATED_DATE}.json"
DOC_PATH = ROOT / "docs" / f"102_BINANCE_2021_ACCOUNT_STATEMENT_INCOME_VALUATION_AUDIT_{CREATED_DATE}.md"
USD_STABLES = {"BUSD", "DAI", "FDUSD", "TUSD", "USDC", "USDD", "USDP", "USDT"}


def main() -> None:
    rows = build_rows()
    row_results = [value_row(row) for row in rows]
    audit = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "row_count": len(rows),
        "coverage": summarize(row_results),
        "asset_summary": summarize_by_asset(row_results),
        "unpriced_samples": [row for row in row_results if not row["has_valuation"]][:25],
        "priced_samples": [row for row in row_results if row["has_valuation"]][:25],
        "interpretation": build_interpretation(row_results),
    }
    JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(render_doc(audit), encoding="utf-8")
    print(json.dumps({"json": str(JSON_PATH), "doc": str(DOC_PATH), "coverage": audit["coverage"]}, ensure_ascii=False, indent=2))


def value_row(row: dict[str, Any]) -> dict[str, Any]:
    asset = str(row.get("asset") or "").upper().strip()
    quantity = dec(row.get("quantity"))
    date = str(row.get("timestamp_utc") or "")[:10]
    price_row = stable_price_row(asset) if asset in USD_STABLES else lookup_rate(date, asset, "USD")
    fx_row = lookup_rate(date, "USD", "EUR")
    price_usd = dec(price_row.get("rate")) if price_row else Decimal("0")
    fx = dec(fx_row.get("rate")) if fx_row else Decimal("0")
    value_usd = quantity * price_usd if price_usd > 0 else Decimal("0")
    value_eur = value_usd * fx if fx > 0 else Decimal("0")
    return {
        "timestamp_utc": row.get("timestamp_utc"),
        "date": date,
        "asset": asset,
        "quantity": plain(quantity),
        "event_type": row.get("event_type"),
        "has_asset_price_usd": price_usd > 0,
        "has_usd_eur_fx": fx > 0,
        "has_valuation": price_usd > 0 and fx > 0,
        "price_usd": plain(price_usd),
        "price_source": price_row.get("source") if price_row else "",
        "price_rate_date": price_row.get("rate_date") if price_row else "",
        "usd_eur_fx": plain(fx),
        "fx_source": fx_row.get("source") if fx_row else "",
        "fx_rate_date": fx_row.get("rate_date") if fx_row else "",
        "value_usd": plain(value_usd),
        "value_eur": plain(value_eur),
        "tx_id": row.get("tx_id"),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_usd = sum((dec(row["value_usd"]) for row in rows), Decimal("0"))
    total_eur = sum((dec(row["value_eur"]) for row in rows), Decimal("0"))
    priced = sum(1 for row in rows if row["has_valuation"])
    price_missing = sum(1 for row in rows if not row["has_asset_price_usd"])
    fx_missing = sum(1 for row in rows if not row["has_usd_eur_fx"])
    return {
        "priced_rows": priced,
        "unpriced_rows": len(rows) - priced,
        "missing_asset_price_rows": price_missing,
        "missing_usd_eur_fx_rows": fx_missing,
        "priced_total_usd": plain(total_usd),
        "priced_total_eur": plain(total_eur),
    }


def summarize_by_asset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        asset = str(row["asset"])
        item = grouped.setdefault(
            asset,
            {
                "rows": 0,
                "priced_rows": 0,
                "quantity_total": Decimal("0"),
                "value_usd_total": Decimal("0"),
                "value_eur_total": Decimal("0"),
                "missing_dates": set(),
            },
        )
        item["rows"] += 1
        if row["has_valuation"]:
            item["priced_rows"] += 1
        else:
            item["missing_dates"].add(row["date"])
        item["quantity_total"] += dec(row["quantity"])
        item["value_usd_total"] += dec(row["value_usd"])
        item["value_eur_total"] += dec(row["value_eur"])
    return {
        asset: {
            "rows": item["rows"],
            "priced_rows": item["priced_rows"],
            "unpriced_rows": item["rows"] - item["priced_rows"],
            "quantity_total": plain(item["quantity_total"]),
            "value_usd_total": plain(item["value_usd_total"]),
            "value_eur_total": plain(item["value_eur_total"]),
            "missing_dates": sorted(item["missing_dates"])[:20],
        }
        for asset, item in sorted(grouped.items())
    }


def build_interpretation(rows: list[dict[str, Any]]) -> list[str]:
    unpriced_assets = sorted({str(row["asset"]) for row in rows if not row["has_valuation"]})
    lines = [
        "Valuation audit only checks rows prepared by the reviewed Binance 2021 income importer.",
        "USDT is valued as a USD stable asset and then converted with cached USD/EUR FX.",
    ]
    if unpriced_assets:
        lines.append(f"Rows for these assets are not fully valued yet: {', '.join(unpriced_assets)}.")
        if "NFT" in unpriced_assets:
            lines.append("The Binance symbol NFT likely needs explicit APENFT/NFT price mapping or manual evidence before import with EUR value.")
    else:
        lines.append("All prepared rows have cached asset USD prices and USD/EUR FX coverage.")
    return lines


def render_doc(audit: dict[str, Any]) -> str:
    lines = [
        "# Binance 2021 Account Statement Income Valuation Audit - 2026-05-09",
        "",
        "## Zweck",
        "",
        "Pruefung, ob die isolierten Binance-Account-Statement-Ertragszeilen vor einem steuerwirksamen Import bewertbar sind.",
        "",
        "## Coverage",
        "",
        f"- Zeilen: `{audit['row_count']}`",
        f"- Bewertet: `{audit['coverage']['priced_rows']}`",
        f"- Unbewertet: `{audit['coverage']['unpriced_rows']}`",
        f"- Fehlende Asset-USD-Preise: `{audit['coverage']['missing_asset_price_rows']}`",
        f"- Fehlende USD/EUR-FX: `{audit['coverage']['missing_usd_eur_fx_rows']}`",
        f"- Bewerteter Gesamtwert USD: `{audit['coverage']['priced_total_usd']}`",
        f"- Bewerteter Gesamtwert EUR: `{audit['coverage']['priced_total_eur']}`",
        "",
        "## Asset Summary",
        "",
    ]
    for asset, item in audit["asset_summary"].items():
        lines.append(
            f"- `{asset}`: rows={item['rows']}, priced={item['priced_rows']}, unpriced={item['unpriced_rows']}, "
            f"qty={item['quantity_total']}, value_eur={item['value_eur_total']}"
        )
        if item["missing_dates"]:
            lines.append(f"  - Missing dates sample: `{item['missing_dates']}`")
    lines += ["", "## Bewertung", ""]
    lines.extend(f"- {line}" for line in audit["interpretation"])
    lines += [
        "",
        "## Import-Entscheidung",
        "",
        "ADA, DOGE und USDT sind als bewertbare Kleinertraege technisch importfaehig; aktueller Importstatus siehe Report 101.",
        "NFT/APENFT bleibt blockiert, bis Symbolmapping oder Preisbeleg geklaert ist.",
    ]
    return "\n".join(lines) + "\n"


def lookup_rate(date: str, base: str, quote: str) -> dict[str, Any] | None:
    if not date or not base:
        return None
    row = STORE.get_fx_rate(rate_date=date, base_ccy=base, quote_ccy=quote)
    if row is None:
        row = STORE.get_fx_rate_on_or_before(rate_date=date, base_ccy=base, quote_ccy=quote)
    return row


def stable_price_row(asset: str) -> dict[str, Any]:
    return {
        "rate_date": "",
        "base_ccy": asset,
        "quote_ccy": "USD",
        "rate": "1",
        "source": "stable_asset_policy",
        "source_rate_date": "",
    }


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def plain(value: Decimal) -> str:
    return value.normalize().to_eng_string() if value else "0"


if __name__ == "__main__":
    main()
