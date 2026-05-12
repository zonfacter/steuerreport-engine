from __future__ import annotations

import hashlib
from typing import Any


def build_transfer_chain_index(matches: list[dict[str, Any]]) -> dict[str, str]:
    """Baue deterministische Chain-IDs fuer zusammenhaengende Transfer-Matches."""
    parent: dict[str, str] = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if left_root < right_root:
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    for match in matches:
        outbound = str(match.get("outbound_event_id", "")).strip()
        inbound = str(match.get("inbound_event_id", "")).strip()
        if not outbound or not inbound:
            continue
        union(outbound, inbound)

    groups: dict[str, list[str]] = {}
    for node in list(parent):
        groups.setdefault(find(node), []).append(node)

    chain_by_event_id: dict[str, str] = {}
    for event_ids in groups.values():
        ordered = sorted(set(event_ids))
        suffix = hashlib.sha256("|".join(ordered).encode("utf-8")).hexdigest()[:16]
        chain_id = f"transfer-chain:{suffix}"
        for event_id in ordered:
            chain_by_event_id[event_id] = chain_id
    return chain_by_event_id
