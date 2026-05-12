from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from tax_engine.admin.service import resolve_effective_runtime_config
from tax_engine.api.dashboard import (
    _load_ignored_tokens,
    _load_token_aliases,
    _normalize_mint,
    _payload_asset_canonical_symbol,
)
from tax_engine.ingestion.store import STORE
from tax_engine.integrations import filter_events_for_processing
from tax_engine.queue import apply_review_actions, apply_tax_event_overrides

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "var" / "chronological_balance_break_audit_current.json"
DEFAULT_MD = ROOT / "docs" / "35_CHRONOLOGICAL_BALANCE_BREAK_AUDIT_CURRENT.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Chronological balance break audit from 2020 onward.")
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--top-assets", type=int, default=20)
    parser.add_argument("--context-days", type=int, default=7)
    parser.add_argument("--ai", action="store_true")
    parser.add_argument("--ai-top", type=int, default=8)
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    events = _effective_events()
    token_aliases = _load_token_aliases()
    ignored_mints = set(_load_ignored_tokens().keys())
    movements = [
        movement
        for row in events
        for movement in _movements(row, token_aliases=token_aliases, ignored_mints=ignored_mints)
    ]
    movements = [row for row in movements if _year(row["timestamp"]) >= args.start_year]
    movements.sort(key=_movement_sort_key)

    audit = _build_audit(movements, top_assets=args.top_assets, context_days=args.context_days)
    if args.ai:
        audit["ai"] = _run_ai_reviews(audit, ai_top=args.ai_top)
    else:
        audit["ai"] = {"enabled": False, "reviews": []}

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(audit, output_json=output_json), encoding="utf-8")
    print(json.dumps({"output_json": str(output_json), "output_md": str(output_md)}, ensure_ascii=False))


def _effective_events() -> list[dict[str, Any]]:
    raw_events = STORE.list_raw_events()
    reviewed, _review_summary = apply_review_actions(raw_events)
    effective, _override_count = apply_tax_event_overrides(reviewed)
    filtered, _filter_summary = filter_events_for_processing(effective, {"include_reference_sources": False})
    return filtered


def _movements(
    event: dict[str, Any],
    *,
    token_aliases: dict[str, dict[str, str]] | None = None,
    ignored_mints: set[str] | None = None,
) -> list[dict[str, Any]]:
    payload = event.get("payload", {})
    if not isinstance(payload, dict):
        return []
    timestamp = str(payload.get("timestamp_utc") or payload.get("timestamp") or "")
    if len(timestamp) < 10:
        return []
    raw_asset = str(payload.get("asset") or payload.get("symbol") or payload.get("base_asset") or "")
    if ignored_mints and _normalize_mint(raw_asset) in ignored_mints:
        return []
    asset = _payload_asset_canonical_symbol(payload, token_aliases)
    if ignored_mints and _normalize_mint(asset) in ignored_mints:
        return []
    if not asset:
        return []
    qty = _quantity(payload)
    source = str(payload.get("source") or "").lower().strip()
    event_type = str(payload.get("event_type") or "").lower().strip()
    if event_type.startswith("derivative") or source in {"jupiter_perps"}:
        return []
    side = str(payload.get("side") or "").lower().strip()
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    template = {
        "event_id": str(event.get("unique_event_id") or ""),
        "timestamp": timestamp,
        "day": timestamp[:10],
        "year": _year(timestamp),
        "source": str(payload.get("source") or ""),
        "event_type": str(payload.get("event_type") or ""),
        "tx_id": str(payload.get("tx_id") or ""),
        "raw_label": str(raw.get("Label") or raw.get("label") or ""),
        "raw_comment": str(raw.get("Comment (optional)") or raw.get("comment") or ""),
        "raw_integration": str(raw.get("Integration Name") or raw.get("integration") or ""),
    }
    movements: list[dict[str, Any]] = []

    def add(asset_symbol: str, delta: Decimal, movement_side: str, quantity: Decimal) -> None:
        if not asset_symbol or delta == 0:
            return
        movements.append(
            {
                **template,
                "asset": asset_symbol,
                "delta": delta,
                "abs_delta": abs(delta),
                "side": movement_side,
                "quantity": abs(quantity),
            }
        )

    if _is_spot_pair_trade(payload):
        quote_asset = str(payload.get("quote_asset") or "").upper().strip()
        quote_qty = _quote_quantity(payload)
        if side == "buy":
            add(asset, abs(qty), "buy_base", qty)
            add(quote_asset, -abs(quote_qty), "buy_quote", quote_qty)
        elif side == "sell":
            add(asset, -abs(qty), "sell_base", qty)
            add(quote_asset, abs(quote_qty), "sell_quote", quote_qty)
        fee_asset = str(payload.get("fee_asset") or "").upper().strip()
        fee_qty = _decimal(payload.get("fee"))
        add(fee_asset, -abs(fee_qty), "fee", fee_qty)
        return movements

    if side in {"in", "buy"}:
        add(asset, abs(qty), side, qty)
    elif side in {"out", "sell"}:
        add(asset, -abs(qty), side, qty)
    else:
        add(asset, qty, side or "neutral", qty)
    return movements


def _movement_sort_key(row: dict[str, Any]) -> tuple[str, int, str]:
    return (str(row.get("timestamp") or ""), _movement_sort_priority(row), str(row.get("event_id") or ""))


def _movement_sort_priority(row: dict[str, Any]) -> int:
    delta = _decimal(row.get("delta"))
    side = str(row.get("side") or "").lower().strip()
    event_type = str(row.get("event_type") or "").lower().strip()
    if delta > 0:
        return 0
    if side in {"in", "buy_base", "sell_quote"}:
        return 0
    if event_type in {"fee"} or side == "fee":
        return 3
    if delta < 0:
        return 2
    return 1


def _is_spot_pair_trade(payload: dict[str, Any]) -> bool:
    base_asset = str(payload.get("base_asset") or "").upper().strip()
    quote_asset = str(payload.get("quote_asset") or "").upper().strip()
    side = str(payload.get("side") or "").lower().strip()
    event_type = str(payload.get("event_type") or "").lower().strip()
    return bool(base_asset and quote_asset and side in {"buy", "sell"} and event_type in {"trade", "spot_trade", "order"})


def _quote_quantity(payload: dict[str, Any]) -> Decimal:
    raw = payload.get("raw_row") if isinstance(payload.get("raw_row"), dict) else {}
    for key in ("quote_quantity", "quote_amount", "quoteQty", "cummulativeQuoteQty", "quote_qty"):
        value = payload.get(key)
        if value is None and raw:
            value = raw.get(key)
        parsed = _decimal(value)
        if parsed != 0:
            return abs(parsed)
    qty = _quantity(payload)
    price = _decimal(payload.get("price"))
    return abs(qty * price)


def _build_audit(movements: list[dict[str, Any]], *, top_assets: int, context_days: int) -> dict[str, Any]:
    balances: dict[str, Decimal] = defaultdict(Decimal)
    first_negative: dict[str, dict[str, Any]] = {}
    min_balance: dict[str, dict[str, Any]] = {}
    yearly_net: dict[str, dict[int, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    source_net: dict[str, Counter[tuple[str, str, str]]] = defaultdict(Counter)
    event_count_by_asset: Counter[str] = Counter()

    for row in movements:
        asset = row["asset"]
        before = balances[asset]
        after = before + row["delta"]
        balances[asset] = after
        row["balance_before"] = before
        row["balance_after"] = after
        yearly_net[asset][row["year"]] += row["delta"]
        source_net[asset][(row["source"], row["event_type"], row["side"])] += row["delta"]
        event_count_by_asset[asset] += 1
        if before >= 0 > after and asset not in first_negative:
            first_negative[asset] = _slim_movement(row)
        current_min = min_balance.get(asset)
        if current_min is None or after < _decimal(current_min["balance_after"]):
            min_balance[asset] = _slim_movement(row)

    ranked_assets = sorted(
        balances,
        key=lambda asset: (
            balances[asset] < 0,
            abs(balances[asset]),
            event_count_by_asset[asset],
        ),
        reverse=True,
    )
    asset_reports = []
    movement_by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in movements:
        movement_by_asset[row["asset"]].append(row)

    for asset in ranked_assets[:top_assets]:
        first = first_negative.get(asset)
        worst = min_balance.get(asset)
        focus_ts = str((first or worst or {}).get("timestamp") or "")
        context = _context_for_asset(movement_by_asset[asset], focus_ts=focus_ts, days=context_days)
        asset_reports.append(
            {
                "asset": asset,
                "final_balance": _plain(balances[asset]),
                "event_count": event_count_by_asset[asset],
                "first_negative": first,
                "worst_balance": worst,
                "yearly_net": {str(year): _plain(value) for year, value in sorted(yearly_net[asset].items())},
                "source_net_top": [
                    {
                        "source": key[0],
                        "event_type": key[1],
                        "side": key[2],
                        "net": _plain(value),
                    }
                    for key, value in sorted(source_net[asset].items(), key=lambda item: abs(item[1]), reverse=True)[:20]
                ],
                "context": context,
            }
        )

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "movement_count": len(movements),
        "asset_count": len(balances),
        "negative_final_assets": sum(1 for value in balances.values() if value < 0),
        "asset_reports": asset_reports,
    }


def _context_for_asset(rows: list[dict[str, Any]], *, focus_ts: str, days: int) -> dict[str, Any]:
    focus_dt = _parse_dt(focus_ts)
    if focus_dt is None:
        selected = rows[:30]
    else:
        start = focus_dt - timedelta(days=days)
        end = focus_dt + timedelta(days=days)
        selected = [row for row in rows if (dt := _parse_dt(row["timestamp"])) is not None and start <= dt <= end]
    source_counter: Counter[tuple[str, str, str]] = Counter()
    for row in selected:
        source_counter[(row["source"], row["event_type"], row["side"])] += 1
    return {
        "focus_timestamp": focus_ts,
        "window_days": days,
        "event_count": len(selected),
        "source_counts": [
            {"source": key[0], "event_type": key[1], "side": key[2], "count": count}
            for key, count in source_counter.most_common(12)
        ],
        "events": [_slim_movement(row) for row in selected[:80]],
    }


def _run_ai_reviews(audit: dict[str, Any], *, ai_top: int) -> dict[str, Any]:
    config = resolve_effective_runtime_config().get("runtime", {}).get("ai_review", {})
    base_url = str(config.get("llama_cpp_base_url") or "http://192.168.2.203:11435").rstrip("/")
    model = str(config.get("llama_cpp_model") or "qwen3-coder-30b-a3b-llamacpp")
    timeout = float(config.get("llama_cpp_timeout_seconds") or 180.0)
    reviews = []
    for report in audit.get("asset_reports", [])[:ai_top]:
        prompt = _ai_prompt(report)
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 700,
        }
        try:
            content = _post_chat_completion(f"{base_url}/v1/chat/completions", payload=payload, timeout=timeout)
            reviews.append({"asset": report["asset"], "status": "success", "content": content})
        except Exception as exc:
            reviews.append({"asset": report["asset"], "status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return {"enabled": True, "base_url": base_url, "model": model, "reviews": reviews}


def _ai_prompt(report: dict[str, Any]) -> str:
    compact = {
        "asset": report.get("asset"),
        "final_balance": report.get("final_balance"),
        "first_negative": report.get("first_negative"),
        "worst_balance": report.get("worst_balance"),
        "yearly_net": report.get("yearly_net"),
        "source_net_top": report.get("source_net_top", [])[:12],
        "context_source_counts": (report.get("context") or {}).get("source_counts", [])[:12],
        "context_events": (report.get("context") or {}).get("events", [])[:30],
    }
    return (
        "Du bist Plausibilitaetspruefer fuer deutsche Krypto-Steuerdaten. "
        "Analysiere chronologisch den ersten negativen Bestand. "
        "Antworte knapp als JSON mit keys: probable_cause, confidence, evidence, next_checks, safe_automatic_actions, needs_user_data. "
        "Empfiehl keine pauschalen Loeschungen ohne Primaerbeleg.\n\n"
        f"DATEN:\n{json.dumps(compact, ensure_ascii=False)}"
    )


def _post_chat_completion(url: str, *, payload: dict[str, Any], timeout: float) -> str:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        decoded = json.loads(response.read().decode("utf-8"))
    content = decoded.get("choices", [{}])[0].get("message", {}).get("content", "")
    return str(content).strip()


def _render_markdown(audit: dict[str, Any], *, output_json: Path) -> str:
    lines = [
        "# Chronologische Bestandsbruch-Analyse",
        "",
        f"Generiert: `{audit['generated_at_utc']}`",
        f"JSON: `{output_json}`",
        "",
        "## Überblick",
        "",
        f"- Bewegungen: `{audit['movement_count']}`",
        f"- Assets: `{audit['asset_count']}`",
        f"- Assets mit negativem Endbestand: `{audit['negative_final_assets']}`",
        "",
        "## Asset-Befunde",
        "",
    ]
    for report in audit.get("asset_reports", []):
        first = report.get("first_negative") or {}
        worst = report.get("worst_balance") or {}
        lines.extend(
            [
                f"### {report['asset']}",
                "",
                f"- Endbestand Modell: `{report['final_balance']}`",
                f"- Events: `{report['event_count']}`",
                f"- Erster Negativbestand: `{first.get('timestamp', '')}` nach `{first.get('event_id', '')}`",
                f"- Auslösend: `{first.get('source', '')}` / `{first.get('event_type', '')}` / `{first.get('side', '')}` / `{first.get('delta', '')}`",
                f"- Schlimmster Stand: `{worst.get('balance_after', '')}` am `{worst.get('timestamp', '')}`",
                "",
                "Jahres-Netto:",
            ]
        )
        for year, value in report.get("yearly_net", {}).items():
            lines.append(f"- `{year}`: `{value}`")
        lines.extend(["", "Top Quellen-Netto:"])
        for row in report.get("source_net_top", [])[:10]:
            lines.append(f"- `{row['source']}` / `{row['event_type']}` / `{row['side']}`: `{row['net']}`")
        lines.append("")
    ai = audit.get("ai") or {}
    if ai.get("enabled"):
        lines.extend(["## Lokale KI-Auswertung", ""])
        lines.append(f"- Modell: `{ai.get('model')}`")
        lines.append(f"- Endpoint: `{ai.get('base_url')}`")
        lines.append("")
        for review in ai.get("reviews", []):
            lines.append(f"### KI: {review.get('asset')}")
            lines.append("")
            if review.get("status") == "success":
                lines.append("```json")
                lines.append(str(review.get("content") or "").strip())
                lines.append("```")
            else:
                lines.append(f"- Fehler: `{review.get('error')}`")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _slim_movement(row: dict[str, Any]) -> dict[str, str]:
    keys = (
        "event_id",
        "timestamp",
        "asset",
        "source",
        "event_type",
        "side",
        "quantity",
        "delta",
        "balance_before",
        "balance_after",
        "tx_id",
        "raw_integration",
        "raw_label",
        "raw_comment",
    )
    result = {}
    for key in keys:
        value = row.get(key, "")
        result[key] = _plain(value) if isinstance(value, Decimal) else str(value)
    return result


def _quantity(payload: dict[str, Any]) -> Decimal:
    heliumgeek_qty = _heliumgeek_display_quantity(payload)
    if heliumgeek_qty > Decimal("0"):
        return heliumgeek_qty
    for key in ("quantity", "amount", "qty", "size"):
        if key in payload:
            value = _decimal(payload.get(key))
            if value != 0:
                return abs(value)
    return Decimal("0")


def _heliumgeek_display_quantity(payload: dict[str, Any]) -> Decimal:
    if str(payload.get("source", "")).lower().strip() != "heliumgeek":
        return Decimal("0")
    raw_row = payload.get("raw_row")
    if not isinstance(raw_row, dict):
        return Decimal("0")
    asset = str(payload.get("asset") or "").upper().strip()
    for token_field, amount_field in (
        ("HNT Token", "HNT Tokens"),
        ("IOT Token", "IOT Tokens"),
        ("MOBILE Token", "MOBILE Tokens"),
    ):
        if str(raw_row.get(token_field, "")).upper().strip() != asset:
            continue
        value = _decimal(raw_row.get(amount_field))
        if value != Decimal("0"):
            return abs(value)
    return Decimal("0")


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0").replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _parse_dt(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _year(timestamp: str) -> int:
    try:
        return int(str(timestamp)[:4])
    except ValueError:
        return 0


def _plain(value: Decimal | Any) -> str:
    if isinstance(value, Decimal):
        return value.to_eng_string()
    return str(value)


if __name__ == "__main__":
    main()
