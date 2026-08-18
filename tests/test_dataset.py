"""Tests for dataset preparation and ArangoDB query translation."""

from __future__ import annotations

from pathlib import Path

import pytest

from graph_bench.dataset.prepare import _barabasi_albert, _write_csv


# ── Barabási–Albert graph generator ──────────────────────────────────────────

def test_barabasi_albert_reproducible():
    e1, n1, _d1 = _barabasi_albert(200, 500, seed=42)
    e2, n2, _d2 = _barabasi_albert(200, 500, seed=42)
    assert e1 == e2
    assert n1 == n2
    assert len(e1) == 500
    assert len(n1) >= 2


def test_barabasi_albert_target_size():
    edges, nodes, degree = _barabasi_albert(500, 1000, seed=7)
    assert len(edges) == 1000
    # All edge endpoints must be in seen_nodes
    for src, dst in edges:
        assert src in nodes
        assert dst in nodes


def test_barabasi_albert_no_self_loops():
    edges, nodes, _ = _barabasi_albert(100, 300, seed=1)
    for src, dst in edges:
        assert src != dst, f"Self-loop found: {src} -> {dst}"


def test_barabasi_albert_different_seeds_differ():
    e1, _, _ = _barabasi_albert(200, 500, seed=1)
    e2, _, _ = _barabasi_albert(200, 500, seed=99)
    assert e1 != e2


# ── CSV writer ────────────────────────────────────────────────────────────────

def test_write_csv(tmp_path: Path):
    edges = [(1, 2), (2, 3), (3, 1)]
    nodes = {1, 2, 3}
    degree = {1: 2, 2: 2, 3: 2}
    nodes_csv = tmp_path / "nodes.csv"
    edges_csv = tmp_path / "edges.csv"
    _write_csv(nodes_csv, edges_csv, edges, nodes, degree)

    assert nodes_csv.exists() and edges_csv.exists()

    node_lines = nodes_csv.read_text().strip().splitlines()
    assert node_lines[0] == "id,community"
    assert len(node_lines) == 4  # header + 3 nodes

    edge_lines = edges_csv.read_text().strip().splitlines()
    assert edge_lines[0] == "src,dst"
    assert len(edge_lines) == 4  # header + 3 edges


# ── ArangoDB query translation ────────────────────────────────────────────────

def test_arango_translate_all_queries():
    """Verify ArangoDB adapter translates every shared workload query to valid AQL."""
    import os

    os.environ.setdefault("ARANGO_URL", "http://localhost:8529")
    os.environ.setdefault("ARANGO_PASSWORD", "test")

    from graph_bench.platforms.arangodb import ArangoDBPlatform

    # Instantiate without connecting
    platform = ArangoDBPlatform.__new__(ArangoDBPlatform)
    platform.platform_key = "arangodb"
    platform.platform_name = "ArangoDB"
    platform.batch_size = 1000
    platform.node_label = "Person"
    platform.rel_type = "FRIEND"
    platform.url = "http://localhost:8529"
    platform.db_name = "graph_bench"
    platform.user = "root"
    platform.password = "test"
    platform._client = None
    platform._db = None
    platform.VERTICES = "persons"
    platform.EDGES = "friends"

    # 1-hop (exact string from base.py hop_query(1))
    aql, _ = platform._translate(
        "MATCH (n:Person {id: $id})-[:FRIEND]-(m:Person) RETURN count(m) AS cnt", {"id": 1}
    )
    assert "FOR n IN persons" in aql
    assert "1..1" in aql

    # 3-hop (exact string from base.py hop_query(3) — uses count(DISTINCT m))
    aql, _ = platform._translate(
        "MATCH (n:Person {id: $id})-[:FRIEND*1..3]-(m:Person) WHERE m.id <> $id RETURN count(DISTINCT m) AS cnt",
        {"id": 1},
    )
    assert "1..3" in aql

    # Filtered lookup
    aql, _ = platform._translate(
        "MATCH (n:Person) WHERE n.community = $community RETURN n.id AS id LIMIT 25",
        {"community": 3},
    )
    assert "n.community ==" in aql or "n.community == @community" in aql

    # Aggregation
    aql, _ = platform._translate(
        "MATCH (n:Person)-[:FRIEND]-(m:Person) RETURN n.community AS community, count(m) AS friend_count ORDER BY friend_count DESC LIMIT 10",
        {},
    )
    assert "friend_count" in aql or "LET c" in aql

    # Write query
    aql, _ = platform._translate(
        "MATCH (n:Person {id: $id}) SET n.last_access = $ts RETURN n.id",
        {"id": 1, "ts": 123456},
    )
    assert "UPDATE" in aql or "last_access" in aql

    # Point lookup (fallback)
    aql, _ = platform._translate(
        "MATCH (n:Person {id: $id}) RETURN n.community AS community", {"id": 1}
    )
    assert "n.community" in aql
