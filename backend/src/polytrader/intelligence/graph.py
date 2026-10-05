from __future__ import annotations

from collections import defaultdict


class MarketEventGraph:
    """Small typed graph for research relationships, never an execution graph."""

    def __init__(self) -> None:
        self._nodes: dict[str, str] = {}
        self._edges: dict[str, list[tuple[str, str]]] = defaultdict(list)

    def add_market(self, node_id: str, asset_class: str) -> None:
        if asset_class != "polymarket":
            raise ValueError("this graph adapter currently accepts Polymarket markets only")
        self._nodes[node_id] = "market"

    def add_event(self, node_id: str, event_type: str) -> None:
        if not node_id or not event_type:
            raise ValueError("node identity is required")
        self._nodes[node_id] = "event"

    def link(self, source: str, target: str, relation: str) -> None:
        if source not in self._nodes or target not in self._nodes:
            raise KeyError("both graph nodes must exist")
        self._edges[source].append((target, relation))

    def neighbors(self, node_id: str) -> tuple[tuple[str, str], ...]:
        return tuple(self._edges.get(node_id, ()))
