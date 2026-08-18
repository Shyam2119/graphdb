"""Abstract graph database adapter interface."""

from __future__ import annotations

import csv
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from graph_bench.config import get_dataset_config


@dataclass
class LoadMetrics:
    wall_clock_seconds: float
    nodes_loaded: int
    relationships_loaded: int
    nodes_per_second: float
    relationships_per_second: float
    method: str


@dataclass
class FootprintMetrics:
    stored_data_size: str
    memory_usage: str
    instance_specs: str
    notes: str = ""


class GraphPlatform(ABC):
    """Common interface implemented by every database adapter."""

    def __init__(self, platform_key: str, platform_name: str, batch_size: int = 1000):
        self.platform_key = platform_key
        self.platform_name = platform_name
        self.batch_size = batch_size
        ds = get_dataset_config()
        self.node_label = ds.node_label
        self.rel_type = ds.relationship_type

    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def clear_database(self) -> None:
        ...

    @abstractmethod
    def create_schema(self) -> None:
        """Create indexes/constraints required for fair lookup benchmarks."""
        ...

    @abstractmethod
    def load_nodes_batch(self, rows: list[dict[str, Any]]) -> None:
        ...

    @abstractmethod
    def load_edges_batch(self, rows: list[dict[str, Any]]) -> None:
        ...

    @abstractmethod
    def run_query(self, query: str, params: dict[str, Any] | None = None) -> Any:
        ...

    @abstractmethod
    def get_footprint(self) -> FootprintMetrics:
        ...

    def load_from_csv(self, nodes_file: Path, edges_file: Path) -> LoadMetrics:
        """Standard CSV ingest used by every platform for fairness."""
        self.clear_database()
        self.create_schema()

        start = time.perf_counter()
        nodes_loaded = 0
        rels_loaded = 0

        with nodes_file.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            batch: list[dict[str, Any]] = []
            for row in reader:
                batch.append({"id": int(row["id"]), "community": int(row["community"])})
                if len(batch) >= self.batch_size:
                    self.load_nodes_batch(batch)
                    nodes_loaded += len(batch)
                    batch.clear()
            if batch:
                self.load_nodes_batch(batch)
                nodes_loaded += len(batch)

        with edges_file.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            batch = []
            for row in reader:
                batch.append({"src": int(row["src"]), "dst": int(row["dst"])})
                if len(batch) >= self.batch_size:
                    self.load_edges_batch(batch)
                    rels_loaded += len(batch)
                    batch.clear()
            if batch:
                self.load_edges_batch(batch)
                rels_loaded += len(batch)

        elapsed = time.perf_counter() - start
        return LoadMetrics(
            wall_clock_seconds=elapsed,
            nodes_loaded=nodes_loaded,
            relationships_loaded=rels_loaded,
            nodes_per_second=nodes_loaded / elapsed if elapsed else 0.0,
            relationships_per_second=rels_loaded / elapsed if elapsed else 0.0,
            method=self.load_method_name(),
        )

    @abstractmethod
    def load_method_name(self) -> str:
        ...

    def sample_start_nodes(self, count: int) -> list[int]:
        """Return random start node IDs for traversal benchmarks."""
        result = self.run_query(self._sample_nodes_query(count), {"count": count})
        return [int(r) for r in result]

    @abstractmethod
    def _sample_nodes_query(self, count: int) -> str:
        ...

    def hop_query(self, depth: int) -> str:
        label = self.node_label
        rel = self.rel_type
        if depth == 1:
            return (
                f"MATCH (n:{label} {{id: $id}})-[:{rel}]-(m:{label}) "
                "RETURN count(m) AS cnt"
            )
        return (
            f"MATCH (n:{label} {{id: $id}})-[:{rel}*1..{depth}]-(m:{label}) "
            "WHERE m.id <> $id RETURN count(DISTINCT m) AS cnt"
        )

    def point_lookup_query(self) -> str:
        return f"MATCH (n:{self.node_label} {{id: $id}}) RETURN n.community AS community"

    def filtered_lookup_query(self) -> str:
        return (
            f"MATCH (n:{self.node_label}) WHERE n.community = $community "
            "RETURN n.id AS id LIMIT 25"
        )

    def aggregation_query(self) -> str:
        return (
            f"MATCH (n:{self.node_label})-[:{self.rel_type}]-(m:{self.node_label}) "
            "RETURN n.community AS community, count(m) AS friend_count "
            "ORDER BY friend_count DESC LIMIT 10"
        )

    def write_query(self) -> str:
        return (
            f"MATCH (n:{self.node_label} {{id: $id}}) "
            "SET n.last_access = $ts RETURN n.id"
        )

    def read_query(self) -> str:
        return self.point_lookup_query()
