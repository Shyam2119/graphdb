"""FalkorDB platform adapter."""

from __future__ import annotations

import os
import random
from typing import Any

from falkordb import FalkorDB

from graph_bench.platforms.base import FootprintMetrics, GraphPlatform


class FalkorDBPlatform(GraphPlatform):
    GRAPH_NAME = "graph_bench"

    def __init__(self, platform_key: str, platform_name: str, batch_size: int = 1000):
        super().__init__(platform_key, platform_name, batch_size)
        self.host = os.getenv("FALKORDB_HOST", "localhost")
        self.port = int(os.getenv("FALKORDB_PORT", "6379"))
        self._db: FalkorDB | None = None
        self._graph = None

    def connect(self) -> None:
        self._db = FalkorDB(host=self.host, port=self.port)
        self._graph = self._db.select_graph(self.GRAPH_NAME)

    def close(self) -> None:
        self._db = None
        self._graph = None

    def clear_database(self) -> None:
        if self._graph:
            try:
                self._graph.delete()
            except Exception:
                pass
        if self._db:
            self._graph = self._db.select_graph(self.GRAPH_NAME)

    def create_schema(self) -> None:
        label = self.node_label
        for stmt in (
            f"CREATE INDEX FOR (n:{label}) ON (n.id)",
            f"CREATE INDEX FOR (n:{label}) ON (n.community)",
            f"CREATE INDEX ON :{label}(id)",
            f"CREATE INDEX ON :{label}(community)",
        ):
            try:
                self._graph.query(stmt)
            except Exception:
                pass

    def load_nodes_batch(self, rows: list[dict[str, Any]]) -> None:
        self._graph.query(
            "UNWIND $rows AS row "
            f"MERGE (n:{self.node_label} {{id: row.id}}) SET n.community = row.community",
            {"rows": rows},
        )

    def load_edges_batch(self, rows: list[dict[str, Any]]) -> None:
        self._graph.query(
            "UNWIND $rows AS row "
            f"MATCH (a:{self.node_label} {{id: row.src}}), (b:{self.node_label} {{id: row.dst}}) "
            f"MERGE (a)-[:{self.rel_type}]->(b)",
            {"rows": rows},
        )

    def run_query(self, query: str, params: dict[str, Any] | None = None) -> Any:
        result = self._graph.query(query, params or {})
        if not result.result_set:
            return []
        row = result.result_set[0]
        if len(row) == 1:
            return [row[0]]
        return list(result.result_set)

    def get_footprint(self) -> FootprintMetrics:
        try:
            nodes = self._graph.query("MATCH (n) RETURN count(n)").result_set[0][0]
            rels = self._graph.query("MATCH ()-[r]->() RETURN count(r)").result_set[0][0]
            info = self._db.connection.info("memory")
            mem = info.get("used_memory_human", "not observable")
            return FootprintMetrics(
                stored_data_size=f"{nodes:,} nodes, {rels:,} relationships",
                memory_usage=str(mem),
                instance_specs="Docker 0.5 vCPU / 256 MB (see docker-compose.yml)",
            )
        except Exception as exc:
            return FootprintMetrics(
                stored_data_size="not observable",
                memory_usage="not observable",
                instance_specs="Docker capped tier",
                notes=str(exc),
            )

    def load_method_name(self) -> str:
        return f"FalkorDB Cypher UNWIND batch ({self.batch_size} rows/batch)"

    def _sample_nodes_query(self, count: int) -> str:
        return f"MATCH (n:{self.node_label}) RETURN n.id LIMIT $count"

    def sample_start_nodes(self, count: int) -> list[int]:
        result = self._graph.query(self._sample_nodes_query(count), {"count": count * 3})
        ids = [int(r[0]) for r in result.result_set]
        return random.sample(ids, min(count, len(ids)))
