"""In-memory mock platform for dry-run and unit tests."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from graph_bench.platforms.base import FootprintMetrics, GraphPlatform


class MockPlatform(GraphPlatform):
    """Tiny adjacency-list graph used to exercise the harness without a database."""

    def __init__(self, platform_key: str = "mock", platform_name: str = "Mock", batch_size: int = 1000):
        super().__init__(platform_key, platform_name, batch_size)
        self.nodes: dict[int, dict[str, Any]] = {}
        self.adj: dict[int, set[int]] = defaultdict(set)

    def connect(self) -> None:
        return None

    def close(self) -> None:
        return None

    def clear_database(self) -> None:
        self.nodes.clear()
        self.adj.clear()

    def create_schema(self) -> None:
        return None

    def load_nodes_batch(self, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            self.nodes[int(row["id"])] = {"community": int(row["community"])}

    def load_edges_batch(self, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            src, dst = int(row["src"]), int(row["dst"])
            self.adj[src].add(dst)
            self.adj[dst].add(src)

    def run_query(self, query: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}
        # Aggregation: must come before traversal check because it also contains "count(m)"
        if "friend_count" in query:
            ranked = sorted(
                (
                    {"community": n.get("community", 0), "friend_count": len(self.adj.get(i, ()))}
                    for i, n in self.nodes.items()
                ),
                key=lambda r: r["friend_count"],
                reverse=True,
            )
            return ranked[:10]
        if "AS cnt" in query or "count(DISTINCT" in query:
            nid = int(params["id"])
            depth = 3 if "1..3" in query else (2 if "1..2" in query else 1)
            seen = self._neighbors(nid, depth)
            seen.discard(nid)
            return [len(seen)]
        if "count(m) AS cnt" in query and "FRIEND" in query and "id" in params:
            nid = int(params["id"])
            return [len(self.adj.get(nid, ()))]
        if "n.community = $community" in query:
            comm = int(params["community"])
            ids = [i for i, n in self.nodes.items() if n.get("community") == comm][:25]
            return [{"id": i} for i in ids]
        if "SET n.last_access" in query or "last_access" in query:
            nid = int(params["id"])
            if nid in self.nodes:
                self.nodes[nid]["last_access"] = params.get("ts")
            return [nid]
        if "RETURN n.id AS id" in query or "RETURN n.id LIMIT" in query:
            return list(self.nodes.keys())[: int(params.get("count", 50))]
        nid = int(params["id"])
        return [self.nodes.get(nid, {}).get("community", 0)]

    def _neighbors(self, start: int, depth: int) -> set[int]:
        frontier = {start}
        seen = {start}
        for _ in range(depth):
            nxt: set[int] = set()
            for node in frontier:
                nxt.update(self.adj.get(node, ()))
            nxt -= seen
            seen |= nxt
            frontier = nxt
        return seen

    def get_footprint(self) -> FootprintMetrics:
        return FootprintMetrics(
            stored_data_size=f"{len(self.nodes)} nodes, {sum(len(v) for v in self.adj.values()) // 2} edges",
            memory_usage="in-process Python",
            instance_specs="mock (not a real database)",
        )

    def load_method_name(self) -> str:
        return "in-memory adjacency list (dry-run)"

    def _sample_nodes_query(self, count: int) -> str:
        return "MATCH (n:Person) RETURN n.id AS id LIMIT $count"
