from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from tax_engine.rulesets.models import TaxRuleset


def _normalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return value.to_eng_string()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in sorted(value.items(), key=lambda i: str(i[0]))}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, tuple):
        return [_normalize(v) for v in value]
    if isinstance(value, set):
        normalized_items = [_normalize(v) for v in value]
        return sorted(normalized_items, key=lambda item: json.dumps(item, sort_keys=True))
    return value


def canonical_json(payload: Mapping[str, Any]) -> str:
    normalized = _normalize(payload)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def event_fingerprint(payload: Mapping[str, Any]) -> str:
    return _sha256(canonical_json(payload))


def ruleset_fingerprint(ruleset: TaxRuleset) -> str:
    return _sha256(canonical_json(asdict(ruleset)))


def config_fingerprint(config: Mapping[str, Any]) -> str:
    return _sha256(canonical_json(config))


def data_fingerprint(event_hashes: Sequence[str]) -> str:
    joined = "|".join(sorted(event_hashes))
    return _sha256(joined)


def report_integrity_id(
    event_hashes: Sequence[str],
    ruleset_hash: str,
    config_hash: str,
) -> str:
    payload = {
        "data_hash": data_fingerprint(event_hashes),
        "ruleset_hash": ruleset_hash,
        "config_hash": config_hash,
    }
    return _sha256(canonical_json(payload))
