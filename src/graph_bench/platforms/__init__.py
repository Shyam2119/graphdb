"""Platform factory."""

from __future__ import annotations

from graph_bench.config import get_platform_specs
from graph_bench.platforms.arangodb import ArangoDBPlatform
from graph_bench.platforms.base import GraphPlatform
from graph_bench.platforms.falkordb import FalkorDBPlatform
from graph_bench.platforms.mock import MockPlatform
from graph_bench.platforms.neo4j import Neo4jPlatform

DRIVER_MAP = {
    # Bolt-compatible platforms all share the same adapter;
    # the platform_key controls which ENV vars and schema syntax to use.
    "neo4j": Neo4jPlatform,
    "cognodb": Neo4jPlatform,
    "memgraph": Neo4jPlatform,
    "falkordb": FalkorDBPlatform,
    "arango": ArangoDBPlatform,
    "mock": MockPlatform,
}


def create_platform(platform_key: str, batch_size: int = 1000) -> GraphPlatform:
    if platform_key == "mock":
        return MockPlatform(batch_size=batch_size)
    specs = get_platform_specs()
    if platform_key not in specs:
        raise KeyError(f"Unknown platform: {platform_key}")
    spec = specs[platform_key]
    cls = DRIVER_MAP.get(spec.driver)
    if cls is None:
        raise ValueError(f"No adapter for driver {spec.driver}")
    return cls(spec.key, spec.name, batch_size=batch_size)
