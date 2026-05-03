from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from tax_engine.core.reconciliation import auto_match_transfers, extract_transfer_events
from tax_engine.ingestion.store import STORE
from tax_engine.reconciliation.chains import build_transfer_chain_index


def _matched_event_ids() -> set[str]:
    ids: set[str] = set()
    for match in STORE.list_transfer_matches():
        ids.add(match["outbound_event_id"])
        ids.add(match["inbound_event_id"])
    return ids


def auto_match_and_persist(
    time_window_seconds: int,
    amount_tolerance_ratio: float,
    min_confidence: float,
) -> dict[str, Any]:
    raw_events = STORE.list_raw_events()
    transfer_events = extract_transfer_events(raw_events)
    result = auto_match_transfers(
        transfer_events=transfer_events,
        matched_event_ids=_matched_event_ids(),
        time_window_seconds=time_window_seconds,
        amount_tolerance_ratio=Decimal(str(amount_tolerance_ratio)),
        min_confidence=Decimal(str(min_confidence)),
    )

    persisted_match_ids: list[str] = []
    for match in result["matches"]:
        persisted_match_ids.append(
            STORE.create_transfer_match(
                outbound_event_id=match["outbound_event_id"],
                inbound_event_id=match["inbound_event_id"],
                confidence_score=match["confidence_score"],
                time_diff_seconds=match["time_diff_seconds"],
                amount_diff=match["amount_diff"],
                status="matched",
                method="auto",
            )
        )

    return {
        "persisted_match_count": len(persisted_match_ids),
        "persisted_match_ids": persisted_match_ids,
        "matches": result["matches"],
        "unmatched_outbound_ids": result["unmatched_outbound_ids"],
        "unmatched_inbound_ids": result["unmatched_inbound_ids"],
    }


def list_unmatched_transfers(
    time_window_seconds: int,
    amount_tolerance_ratio: float,
    min_confidence: float,
) -> dict[str, Any]:
    raw_events = STORE.list_raw_events()
    transfer_events = extract_transfer_events(raw_events)
    result = auto_match_transfers(
        transfer_events=transfer_events,
        matched_event_ids=_matched_event_ids(),
        time_window_seconds=time_window_seconds,
        amount_tolerance_ratio=Decimal(str(amount_tolerance_ratio)),
        min_confidence=Decimal(str(min_confidence)),
    )
    return {
        "unmatched_outbound_ids": result["unmatched_outbound_ids"],
        "unmatched_inbound_ids": result["unmatched_inbound_ids"],
        "candidate_auto_matches": result["matches"],
    }


def manual_match(outbound_event_id: str, inbound_event_id: str, note: str | None) -> dict[str, Any]:
    raw_event_ids = {event["unique_event_id"] for event in STORE.list_raw_events()}
    if outbound_event_id not in raw_event_ids or inbound_event_id not in raw_event_ids:
        return {"ok": False, "error": "event_not_found"}

    match_id = STORE.create_transfer_match(
        outbound_event_id=outbound_event_id,
        inbound_event_id=inbound_event_id,
        confidence_score="1.0000",
        time_diff_seconds=0,
        amount_diff="0",
        status="matched",
        method="manual",
        note=note,
    )
    return {"ok": True, "match_id": match_id}


def list_transfer_ledger(limit: int = 200, offset: int = 0) -> dict[str, Any]:
    rows = _build_transfer_ledger_rows()
    total_count = len(rows)
    start = max(offset, 0)
    end = start + max(limit, 1)
    page = rows[start:end]
    return {
        "total_count": total_count,
        "offset": start,
        "limit": max(limit, 1),
        "rows": page,
    }


def get_transfer_chain(transfer_chain_id: str) -> dict[str, Any] | None:
    chain_id = str(transfer_chain_id or "").strip()
    if not chain_id:
        return None
    rows = [row for row in _build_transfer_ledger_rows() if str(row.get("transfer_chain_id", "")) == chain_id]
    if not rows:
        return None
    rows.sort(key=lambda item: str(item.get("timestamp_utc", "")))
    assets = sorted({str(row.get("asset", "")) for row in rows if str(row.get("asset", ""))})
    wallets: list[str] = []
    for row in rows:
        for key in ("from_depot_id", "to_depot_id"):
            value = str(row.get(key, "")).strip()
            if value and value not in wallets:
                wallets.append(value)
    return {
        "transfer_chain_id": chain_id,
        "row_count": len(rows),
        "asset_count": len(assets),
        "assets": assets,
        "wallet_path": wallets,
        "first_timestamp_utc": rows[0].get("timestamp_utc", ""),
        "last_timestamp_utc": rows[-1].get("timestamp_utc", ""),
        "holding_period_continues": all(str(row.get("holding_period_continues", "")).lower() == "true" for row in rows),
        "rows": rows,
    }


def _build_transfer_ledger_rows() -> list[dict[str, Any]]:
    raw_events = STORE.list_raw_events()
    transfer_events = extract_transfer_events(raw_events)
    matches = STORE.list_transfer_matches()
    match_by_outbound = {str(item["outbound_event_id"]): item for item in matches}
    inbound_matched_ids = {str(item["inbound_event_id"]) for item in matches}
    transfer_chain_by_event_id = build_transfer_chain_index(matches)

    transfer_ids = [str(item.unique_event_id) for item in transfer_events]
    detail_by_id = _load_event_details(transfer_ids)

    rows: list[dict[str, Any]] = []
    for event in transfer_events:
        event_id = str(event.unique_event_id)
        detail = detail_by_id.get(event_id, {})
        payload = detail.get("payload", {}) if isinstance(detail.get("payload"), dict) else {}
        source_name = str(detail.get("source_name") or payload.get("source") or "")
        side = str(payload.get("side") or event.direction).lower()
        tx_id = str(payload.get("tx_id") or "")
        wallet = _extract_wallet(payload)
        counterparty = _extract_counterparty(payload, side)
        from_depot = _extract_depot_id(source_name=source_name, wallet=wallet)

        # Outbound: versuche Gegenbuchung und Zielauflösung.
        if event.direction == "out":
            match = match_by_outbound.get(event_id)
            inbound = detail_by_id.get(str(match["inbound_event_id"]), {}) if match else {}
            inbound_payload = inbound.get("payload", {}) if isinstance(inbound.get("payload"), dict) else {}
            to_platform = str(inbound.get("source_name") or inbound_payload.get("source") or "")
            to_wallet = _extract_wallet(inbound_payload)
            to_counterparty = _extract_counterparty(inbound_payload, "in")
            to_depot = _extract_depot_id(source_name=to_platform, wallet=to_wallet)
            rows.append(
                {
                    "event_id": event_id,
                    "timestamp_utc": _normalize_timestamp(event.timestamp),
                    "asset": event.asset,
                    "quantity": event.amount.to_eng_string(),
                    "direction": "out",
                    "status": "matched" if match else "unmatched_outbound",
                    "from_platform": source_name,
                    "from_wallet": wallet,
                    "from_counterparty": counterparty,
                    "from_depot_id": from_depot,
                    "to_platform": to_platform,
                    "to_wallet": to_wallet,
                    "to_counterparty": to_counterparty,
                    "to_depot_id": to_depot,
                    "tx_id": tx_id,
                    "match_id": str(match["match_id"]) if match else "",
                    "transfer_chain_id": transfer_chain_by_event_id.get(event_id, ""),
                    "method": str(match["method"]) if match else "",
                    "confidence_score": str(match["confidence_score"]) if match else "",
                    "time_diff_seconds": int(match["time_diff_seconds"]) if match else None,
                    "amount_diff": str(match["amount_diff"]) if match else "",
                    "holding_period_continues": "true" if match else "unknown",
                    "continuity_basis": "internal_transfer_matched" if match else "unmatched_transfer",
                }
            )
            continue

        # Inbound: nur anzeigen, wenn keine Outbound-Match-Zeile bereits die Verbindung trägt.
        if event_id in inbound_matched_ids:
            continue
        rows.append(
            {
                "event_id": event_id,
                "timestamp_utc": _normalize_timestamp(event.timestamp),
                "asset": event.asset,
                "quantity": event.amount.to_eng_string(),
                "direction": "in",
                "status": "unmatched_inbound",
                "from_platform": "",
                "from_wallet": "",
                "from_counterparty": _extract_counterparty(payload, "in"),
                "from_depot_id": "",
                "to_platform": source_name,
                "to_wallet": wallet,
                "to_counterparty": "",
                "to_depot_id": from_depot,
                "tx_id": tx_id,
                "match_id": "",
                "transfer_chain_id": transfer_chain_by_event_id.get(event_id, ""),
                "method": "",
                "confidence_score": "",
                "time_diff_seconds": None,
                "amount_diff": "",
                "holding_period_continues": "unknown",
                "continuity_basis": "unmatched_transfer",
            }
        )

    rows.sort(key=lambda item: str(item.get("timestamp_utc", "")), reverse=True)
    return rows


def _load_event_details(event_ids: list[str]) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for event_id in event_ids:
        data = STORE.get_raw_event(event_id)
        if data is not None:
            details[event_id] = data
    return details


def _normalize_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _extract_wallet(payload: dict[str, Any]) -> str:
    for key in ("wallet_address", "wallet", "address", "owner"):
        raw = payload.get(key)
        if raw:
            return str(raw)
    return ""


def _extract_counterparty(payload: dict[str, Any], direction: str) -> str:
    if direction == "out":
        for key in ("to_address", "to_wallet", "destination", "target_address"):
            raw = payload.get(key)
            if raw:
                return str(raw)
    else:
        for key in ("from_address", "from_wallet", "source_address", "sender"):
            raw = payload.get(key)
            if raw:
                return str(raw)
    return ""


def _extract_depot_id(source_name: str, wallet: str) -> str:
    source = str(source_name or "").strip().lower()
    w = str(wallet or "").strip()
    if w:
        return f"{source}:{w}"
    if source:
        return source
    return "unknown"
