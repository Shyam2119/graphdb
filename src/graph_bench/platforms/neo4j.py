"""Neo4j-protocol platform adapter (CognoDB, Neo4j Aura, Memgraph)."""

from __future__ import annotations

import os
import random
from typing import Any

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import ClientError

from graph_bench.platforms.base import FootprintMetrics, GraphPlatform

# Aura Free enforces hard caps; detect these and store as caveats, not crashes.
_AURA_CAP_CODES = {
    "Neo.ClientError.Schema.ConstraintValidationFailed",
    "Neo.ClientError.General.ForbiddenOnReadOnlyDatabase",
}
_AURA_CAP_MESSAGES = (
    "maximum number of nodes",
    "maximum number of relationships",
    "storage quota",
)


class Neo4jPlatform(GraphPlatform):
    """Shared loader for Bolt-compatible graph databases."""

    ENV_MAP = {
        "cognodb": ("COGNODB_URI", "COGNODB_USER", "COGNODB_PASSWORD"),
        "neo4j": ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"),
        "memgraph": ("MEMGRAPH_URI", "MEMGRAPH_USER", "MEMGRAPH_PASSWORD"),
    }

    def __init__(self, platform_key: str, platform_name: str, batch_size: int = 1000):
        super().__init__(platform_key, platform_name, batch_size)
        uri_key, user_key, pass_key = self.ENV_MAP[platform_key]
        self.uri = os.getenv(uri_key, "")
        self.user = os.getenv(user_key, "") or None
        self.password = os.getenv(pass_key, "") or None
        if not self.uri:
            raise ValueError(f"Missing {uri_key} in environment")
        self._driver: Driver | None = None

    def connect(self) -> None:
        auth = (self.user, self.password) if self.user else None
        self._driver = GraphDatabase.driver(self.uri, auth=auth)
        self._driver.verify_connectivity()

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None

    def _session(self):
        if not self._driver:
            raise RuntimeError("Not connected")
        return self._driver.session()

    def clear_database(self) -> None:
        """Batched delete so 256 MB instances do not OOM on DETACH DELETE."""
        while True:
            with self._session() as session:
                result = session.run(
                    "MATCH (n) WITH n LIMIT 2000 DETACH DELETE n RETURN count(n) AS c"
                )
                record = result.single()
                deleted = record["c"] if record else 0
            if not deleted:
                break

    def create_schema(self) -> None:
        label = self.node_label
        if self.platform_key == "memgraph":
            # Memgraph uses the older CREATE INDEX ON syntax
            statements = [
                f"CREATE INDEX ON :{label}(id)",
                f"CREATE INDEX ON :{label}(community)",
            ]
        else:
            # Neo4j 5+ and CognoDB-compatible syntax
            statements = [
                f"CREATE INDEX person_id IF NOT EXISTS FOR (n:{label}) ON (n.id)",
                f"CREATE INDEX person_community IF NOT EXISTS FOR (n:{label}) ON (n.community)",
            ]
        with self._session() as session:
            for stmt in statements:
                try:
                    session.run(stmt)
                except Exception:
                    # Index may already exist — safe to swallow
                    pass

    def load_nodes_batch(self, rows: list[dict[str, Any]]) -> None:
        cypher = (
            "UNWIND $rows AS row "
            f"MERGE (n:{self.node_label} {{id: row.id}}) SET n.community = row.community"
        )
        try:
            with self._session() as session:
                session.run(cypher, rows=rows)
        except ClientError as exc:
            code = getattr(exc, "code", "")
            msg = str(exc).lower()
            if code in _AURA_CAP_CODES or any(m in msg for m in _AURA_CAP_MESSAGES):
                raise RuntimeError(f"Free-tier capacity limit hit during node load: {exc}") from exc
            raise

    def load_edges_batch(self, rows: list[dict[str, Any]]) -> None:
        cypher = (
            "UNWIND $rows AS row "
            f"MATCH (a:{self.node_label} {{id: row.src}}), (b:{self.node_label} {{id: row.dst}}) "
            f"MERGE (a)-[:{self.rel_type}]->(b)"
        )
        try:
            with self._session() as session:
                session.run(cypher, rows=rows)
        except ClientError as exc:
            code = getattr(exc, "code", "")
            msg = str(exc).lower()
            if code in _AURA_CAP_CODES or any(m in msg for m in _AURA_CAP_MESSAGES):
                raise RuntimeError(f"Free-tier capacity limit hit during edge load: {exc}") from exc
            raise

    def run_query(self, query: str, params: dict[str, Any] | None = None) -> Any:
        with self._session() as session:
            result = session.run(query, **(params or {}))
            records = list(result)
            if not records:
                return []
            keys = records[0].keys()
            if "cnt" in keys:
                return [records[0]["cnt"]]
            if "id" in keys and "RETURN n.id AS id" in query:
                return [r["id"] for r in records]
            if "community" in keys and len(keys) == 1:
                return [records[0]["community"]]
            return [r.data() for r in records]

    def get_footprint(self) -> FootprintMetrics:
        try:
            with self._session() as session:
                nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
                rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            memory = (
                "not observable (managed cloud)"
                if self.platform_key != "memgraph"
                else "capped at 256 MB via docker compose"
            )
            return FootprintMetrics(
                stored_data_size=f"{nodes:,} nodes, {rels:,} relationships (logical)",
                memory_usage=memory,
                instance_specs="see config/platforms.yaml",
                notes="Cloud consoles may expose additional metrics.",
            )
        except Exception as exc:
            return FootprintMetrics(
                stored_data_size="not observable",
                memory_usage="not observable",
                instance_specs="see config/platforms.yaml",
                notes=str(exc),
            )

    def load_method_name(self) -> str:
        return f"Neo4j Python driver UNWIND batch MERGE ({self.batch_size} rows/batch)"

    def _sample_nodes_query(self, count: int) -> str:
        return f"MATCH (n:{self.node_label}) RETURN n.id AS id LIMIT $count"

    def sample_start_nodes(self, count: int) -> list[int]:
        """Return a *random* sample of node IDs for traversal benchmarks.

        Fetches 3× the required count from the DB (LIMIT guarantees fast scan),
        then random.sample() picks the final set — ensuring benchmark start nodes
        are not always the same low-ID nodes that happen to be returned first.
        """
        fetch = min(count * 5, 5000)  # fetch a bigger pool for better randomness
        with self._session() as session:
            ids = [r["id"] for r in session.run(self._sample_nodes_query(fetch), count=fetch)]
        if not ids:
            return []
        random.shuffle(ids)
        return [int(i) for i in ids[:count]]
