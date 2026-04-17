from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, dict):
        return {key: _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value


def canonical_payload(payload: dict[str, Any]) -> str:
    canonical = _canonicalize(payload)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def unique_event_id(payload: dict[str, Any]) -> str:
    serialized = canonical_payload(payload)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
