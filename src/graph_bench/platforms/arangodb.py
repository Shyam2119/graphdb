"""ArangoDB platform adapter."""

from __future__ import annotations

import os
import random
from typing import Any

from arango import ArangoClient
from arango.database import StandardDatabase

from graph_bench.platforms.base import FootprintMetrics, GraphPlatform


class ArangoDBPlatform(GraphPlatform):
    VERTICES = "persons"
    EDGES = "friends"

    def __init__(self, platform_key: str, platform_name: str, batch_size: int = 1000):
        super().__init__(platform_key, platform_name, batch_size)
        self.url = os.getenv("ARANGO_URL", "http://localhost:8529")
        self.db_name = os.getenv("ARANGO_DB", "graph_bench")
        self.user = os.getenv("ARANGO_USER", "root")
        self.password = os.getenv("ARANGO_PASSWORD", "")
        self._client: ArangoClient | None = None
        self._db: StandardDatabase | None = None

    def connect(self) -> None:
        self._client = ArangoClient(hosts=self.url)
        sys_db = self._client.db("_system", username=self.user, password=self.password)
        if not sys_db.has_database(self.db_name):
            sys_db.create_database(self.db_name)
        self._db = self._client.db(self.db_name, username=self.user, password=self.password)

    def close(self) -> None:
        self._client = None
        self._db = None

    def clear_database(self) -> None:
        for name in (self.EDGES, self.VERTICES):
            if self._db.has_collection(name):
                self._db.delete_collection(name)
        if self._db.has_graph("social"):
            self._db.delete_graph("social")

    def create_schema(self) -> None:
        if not self._db.has_collection(self.VERTICES):
            self._db.create_collection(self.VERTICES)
        if not self._db.has_collection(self.EDGES):
            self._db.create_collection(self.EDGES, edge=True)
        vcol = self._db.collection(self.VERTICES)
        try:
            vcol.add_persistent_index(fields=["id"], unique=True)
        except Exception:
            pass
        try:
            vcol.add_persistent_index(fields=["community"])
        except Exception:
            pass
        if not self._db.has_graph("social"):
            self._db.create_graph(
                "social",
                edge_definitions=[
                    {
                        "edge_collection": self.EDGES,
                        "from_vertex_collections": [self.VERTICES],
                        "to_vertex_collections": [self.VERTICES],
                    }
                ],
            )

    def load_nodes_batch(self, rows: list[dict[str, Any]]) -> None:
        docs = [{"_key": str(r["id"]), "id": r["id"], "community": r["community"]} for r in rows]
        self._db.collection(self.VERTICES).import_bulk(docs, on_duplicate="update")

    def load_edges_batch(self, rows: list[dict[str, Any]]) -> None:
        docs = [
            {"_from": f"{self.VERTICES}/{r['src']}", "_to": f"{self.VERTICES}/{r['dst']}"}
            for r in rows
        ]
        self._db.collection(self.EDGES).import_bulk(docs, on_duplicate="ignore")

    def run_query(self, query: str, params: dict[str, Any] | None = None) -> Any:
        aql, bind = self._translate(query, params or {})
        cursor = self._db.aql.execute(aql, bind_vars=bind)
        results = list(cursor)
        if not results:
            return [0]
        if len(results) == 1 and isinstance(results[0], (int, float)):
            return [results[0]]
        if len(results) == 1 and isinstance(results[0], dict) and "community" in results[0]:
            return [results[0]["community"]]
        if results and isinstance(results[0], dict) and "cnt" in results[0]:
            return [results[0]["cnt"]]
        return results

    def _translate(self, query: str, params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Map shared Cypher-style workload strings to AQL.

        base.py generates:
          1-hop: MATCH...RETURN count(m) AS cnt        (no *1..)
          2-hop: MATCH...*1..2...RETURN count(DISTINCT m) AS cnt
          3-hop: MATCH...*1..3...RETURN count(DISTINCT m) AS cnt
        """
        bind = dict(params)
        # Multi-hop (2-hop or 3-hop): count(DISTINCT m) or count(m) + variable-length path
        if ("count(DISTINCT m)" in query or ("count(m) AS cnt" in query and "*1.." in query)):
            depth = 3 if "1..3" in query else (2 if "1..2" in query else 1)
            aql = f"""
            FOR n IN {self.VERTICES} FILTER n.id == @id
              FOR v, e IN 1..{depth} ANY n {self.EDGES}
                FILTER v.id != @id
                COLLECT WITH COUNT INTO cnt
                RETURN cnt
            """
            return aql, bind
        # 1-hop: count(m) AS cnt, no variable-length path
        if "count(m) AS cnt" in query:
            aql = f"""
            FOR n IN {self.VERTICES} FILTER n.id == @id
              FOR v IN 1..1 ANY n {self.EDGES}
                COLLECT WITH COUNT INTO cnt
                RETURN cnt
            """
            return aql, bind
        if "n.community = $community" in query:
            aql = f"""
            FOR n IN {self.VERTICES} FILTER n.community == @community
              LIMIT 25
              RETURN {{id: n.id}}
            """
            return aql, bind
        if "friend_count" in query:
            aql = f"""
            FOR n IN {self.VERTICES}
              LET c = LENGTH(FOR v IN 1..1 ANY n {self.EDGES} RETURN 1)
              SORT c DESC
              LIMIT 10
              RETURN {{community: n.community, friend_count: c}}
            """
            return aql, bind
        if "SET n.last_access" in query:
            aql = f"""
            FOR n IN {self.VERTICES} FILTER n.id == @id
              UPDATE n WITH {{last_access: @ts}} IN {self.VERTICES}
              RETURN n.id
            """
            return aql, bind
        aql = f"FOR n IN {self.VERTICES} FILTER n.id == @id RETURN n.community"
        return aql, bind

    def get_footprint(self) -> FootprintMetrics:
        try:
            v = self._db.collection(self.VERTICES).count()
            e = self._db.collection(self.EDGES).count()
            return FootprintMetrics(
                stored_data_size=f"{v:,} vertices, {e:,} edges",
                memory_usage="not observable (community edition)",
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
        return f"ArangoDB import_bulk ({self.batch_size} docs/batch)"

    def _sample_nodes_query(self, count: int) -> str:
        return "unused"

    def sample_start_nodes(self, count: int) -> list[int]:
        cursor = self._db.aql.execute(
            f"FOR n IN {self.VERTICES} LIMIT @count RETURN n.id",
            bind_vars={"count": count * 3},
        )
        ids = [int(x) for x in cursor]
        return random.sample(ids, min(count, len(ids)))
