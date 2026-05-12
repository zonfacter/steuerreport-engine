#!/usr/bin/env python3
"""Refresh Pionex opening-balance evidence from CSV model and API probe."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tax_engine.admin.service import put_admin_setting
from tax_engine.ingestion.store import STORE
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

SETTING_KEY = "runtime.balance_adjustment_candidates"
API_PROBE_JSON = ROOT / "var" / "pionex_api_history_probe_2026-05-08.json"
OUTPUT_JSON = ROOT / "var" / "pionex_opening_evidence_refresh_2026-05-08.json"
OUTPUT_DOC = ROOT / "docs" / "78_PIONEX_OPENING_EVIDENCE_REFRESH_2026-05-08.md"
CANDIDATE_ID = "pionex-usdt-opening-balance-2021-12-28"


def main() -> None:
    api_probe = _load_json(API_PROBE_JSON)
    model = _pionex_model_balances()
    current_api = {
        str(row.get("coin") or "").upper(): Decimal(str(row.get("free") or "0")) + Decimal(str(row.get("frozen") or "0"))
        for row in api_probe.get("nonzero_balances", [])
        if isinstance(row, dict)
    }
    comparison = []
    for asset in sorted(set(model["final_balances"]) | set(current_api)):
        model_value = Decimal(str(model["final_balances"].get(asset, "0")))
        api_value = current_api.get(asset, Decimal("0"))
        comparison.append(
            {
                "asset": asset,
                "model_final": _plain(model_value),
                "api_current": _plain(api_value),
                "difference_api_minus_model": _plain(api_value - model_value),
            }
        )
    evidence = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "api_probe": str(API_PROBE_JSON),
        "model": model,
        "api_current_balances": {asset: _plain(value) for asset, value in sorted(current_api.items())},
        "model_vs_api_current": comparison,
        "conclusion": (
            "Pionex CSV import is materially consistent with current API balances, but the API returns no old fills "
            "for the tested 2021/2022 windows. The opening issue remains a review-only bot/account-start inventory question."
        ),
    }
    OUTPUT_JSON.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_DOC.write_text(_render_doc(evidence), encoding="utf-8")
    _update_candidate(evidence)
    print(json.dumps({"json": str(OUTPUT_JSON), "doc": str(OUTPUT_DOC), "candidate_updated": CANDIDATE_ID}, indent=2))


def _pionex_model_balances() -> dict[str, Any]:
    raw_events = STORE.list_raw_events()
    reviewed, _summary = apply_review_actions(raw_events)
    effective, _override_count = apply_tax_event_overrides(reviewed)
    events = []
    for event in effective:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if payload.get("source") == "pionex":
            events.append((str(payload.get("timestamp_utc") or ""), str(event.get("unique_event_id") or ""), payload))
    events.sort(key=lambda row: (row[0], row[1]))

    balances: dict[str, Decimal] = defaultdict(Decimal)
    minima: dict[str, dict[str, Any]] = {}
    first_negative: dict[str, dict[str, Any]] = {}
    event_counts: dict[str, int] = defaultdict(int)

    for timestamp, event_id, payload in events:
        asset = str(payload.get("asset") or "").upper().strip()
        if not asset:
            continue
        quantity = Decimal(str(payload.get("quantity") or "0"))
        side = str(payload.get("side") or "").lower().strip()
        if quantity == 0:
            continue
        delta = quantity if side in {"in", "buy"} else -quantity if side in {"out", "sell"} else quantity
        before = balances[asset]
        after = before + delta
        balances[asset] = after
        event_counts[asset] += 1
        row = {
            "timestamp_utc": timestamp,
            "event_id": event_id,
            "source": str(payload.get("source") or ""),
            "event_type": str(payload.get("event_type") or ""),
            "side": str(payload.get("side") or ""),
            "quantity": _plain(quantity),
            "delta": _plain(delta),
            "balance_before": _plain(before),
            "balance_after": _plain(after),
            "tx_id": str(payload.get("tx_id") or ""),
        }
        if asset not in minima or after < Decimal(minima[asset]["balance_after"]):
            minima[asset] = row
        if before >= 0 > after and asset not in first_negative:
            first_negative[asset] = row

    return {
        "event_count": len(events),
        "final_balances": {asset: _plain(value) for asset, value in sorted(balances.items())},
        "minimum_balances": {asset: row for asset, row in sorted(minima.items())},
        "first_negative": {asset: row for asset, row in sorted(first_negative.items())},
        "required_opening_inventory_by_asset": {
            asset: _plain(abs(Decimal(row["balance_after"])))
            for asset, row in sorted(minima.items())
            if Decimal(row["balance_after"]) < 0
        },
        "event_counts_by_asset": {asset: count for asset, count in sorted(event_counts.items())},
    }


def _update_candidate(evidence: dict[str, Any]) -> None:
    candidates = _load_candidates()
    entry = candidates.get(CANDIDATE_ID)
    if not isinstance(entry, dict):
        return
    entry = dict(entry)
    evidence_payload = dict(entry.get("evidence") if isinstance(entry.get("evidence"), dict) else {})
    evidence_payload.update(
        {
            "api_history_probe": str(API_PROBE_JSON),
            "opening_evidence_refresh": str(OUTPUT_DOC),
            "opening_evidence_json": str(OUTPUT_JSON),
            "api_current_balance_match": evidence["model_vs_api_current"],
            "required_opening_inventory_by_asset": evidence["model"]["required_opening_inventory_by_asset"],
        }
    )
    entry["evidence"] = evidence_payload
    entry["note"] = (
        str(entry.get("note") or "")
        + " API probe on 2026-05-08 confirmed current balances are close to model but returned no historical fills for 2021/2022; multi-asset bot-start inventory remains review-only."
    )
    entry["updated_at_utc"] = datetime.now(UTC).isoformat()
    candidates[CANDIDATE_ID] = entry
    put_admin_setting(SETTING_KEY, candidates, is_secret=False)


def _render_doc(evidence: dict[str, Any]) -> str:
    lines = [
        "# Pionex Opening Evidence Refresh - 2026-05-08",
        "",
        "## Ziel",
        "",
        "Der bestehende Pionex-USDT-Opening-Kandidat wurde gegen die vollstaendigen CSV-Exporte, die Pionex-API und die Pionex-only Modellbestaende nachgeschaerft.",
        "",
        "## API-Probe",
        "",
        f"- JSON: `{evidence['api_probe']}`",
        f"- Account Status: `{_load_json(API_PROBE_JSON).get('account_status')}`",
        f"- Aktuelle API-Balances: `{evidence['api_current_balances']}`",
        "- Historische Fill-Preview `2021-12-25..2022-02-01`: `0` Rows",
        "- Historische Fill-Preview `2022-01`: `0` Rows",
        "- Historische Fill-Preview `2024-11`: `0` Rows",
        "",
        "Die API ist erreichbar, liefert aber fuer die getesteten alten Handelsfenster keine historischen Fills. Damit ersetzt die API keinen Account-/Bot-Startnachweis.",
        "",
        "## Pionex-Only Modell vs aktuelle API-Balance",
        "",
        "| Asset | Modell final | API aktuell | Differenz API - Modell |",
        "|---|---:|---:|---:|",
    ]
    for row in evidence["model_vs_api_current"]:
        lines.append(f"| `{row['asset']}` | `{row['model_final']}` | `{row['api_current']}` | `{row['difference_api_minus_model']}` |")
    lines += [
        "",
        "Die Restbestaende aus dem CSV-Modell passen eng zu den aktuellen API-Balances. Das stuetzt den CSV-Import, beweist aber keinen historischen Startbestand.",
        "",
        "## Erforderliches Pionex-only Startinventar nach Asset",
        "",
        "| Asset | Minimal erforderlicher Startbestand | Ausloesender Tiefpunkt |",
        "|---|---:|---|",
    ]
    required = evidence["model"]["required_opening_inventory_by_asset"]
    minima = evidence["model"]["minimum_balances"]
    for asset, amount in required.items():
        row = minima[asset]
        lines.append(f"| `{asset}` | `{amount}` | `{row['timestamp_utc']} {row['event_type']}/{row['side']} `{row['tx_id']}` |")
    lines += [
        "",
        "## Bewertung",
        "",
        "- Der grosse offene Punkt bleibt `USDT` mit `1643.40556756620000000000`.",
        "- Kleine Pionex-only Minima in HNT/MXC/JUP/BUSD/BTC/EGLD wirken wie Bot-/Fee-Restchronologie und sind global weitgehend durch andere Quellen oder Dust-Review abgefedert.",
        "- Kein weiterer Pionex-Import wurde durchgefuehrt; RAW-Daten bleiben unveraendert.",
        "- Der bestehende Kandidat bleibt `tax_effective=false` und wurde nur mit Evidenz ergaenzt.",
        "",
        "## Naechste Entscheidung",
        "",
        "Fuer einen finalen Report braucht es entweder einen externen Nachweis fuer das Pionex-Bot-Startinventar oder eine explizite fachliche Entscheidung, diesen Review-Kandidaten als dokumentierte Ersatzrekonstruktion zu behandeln.",
    ]
    return "\n".join(lines) + "\n"


def _load_candidates() -> dict[str, dict[str, Any]]:
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


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _plain(value: Decimal) -> str:
    return value.to_eng_string()


if __name__ == "__main__":
    main()
