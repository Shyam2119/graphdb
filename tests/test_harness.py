"""Tests for graph_bench harness — no live database connections required."""

from __future__ import annotations

from pathlib import Path

import pytest

from graph_bench.metrics import LatencyStats, PlatformResults, percentile_latencies
from graph_bench.platforms.mock import MockPlatform
from graph_bench.report import generate_markdown_report


# ── percentile helpers ────────────────────────────────────────────────────────

def test_percentile_latencies():
    stats = percentile_latencies([1.0, 2.0, 3.0, 4.0, 100.0])
    assert stats.p50_ms == 3.0
    assert stats.p95_ms >= stats.p50_ms
    assert stats.iterations == 5


def test_empty_percentiles():
    stats = percentile_latencies([])
    assert stats.iterations == 0
    assert stats.p50_ms == 0.0


def test_percentile_single_value():
    stats = percentile_latencies([42.0])
    assert stats.p50_ms == pytest.approx(42.0)
    assert stats.p95_ms == pytest.approx(42.0)
    assert stats.iterations == 1


# ── MockPlatform load + queries ───────────────────────────────────────────────

def test_mock_load_and_queries(tmp_path: Path):
    nodes = tmp_path / "nodes.csv"
    edges = tmp_path / "edges.csv"
    nodes.write_text("id,community\n1,0\n2,1\n3,0\n", encoding="utf-8")
    edges.write_text("src,dst\n1,2\n2,3\n", encoding="utf-8")

    platform = MockPlatform()
    platform.connect()
    metrics = platform.load_from_csv(nodes, edges)
    assert metrics.nodes_loaded == 3
    assert metrics.relationships_loaded == 2
    assert metrics.nodes_per_second > 0
    assert metrics.relationships_per_second > 0

    assert platform.run_query(platform.point_lookup_query(), {"id": 1}) == [0]

    hops = platform.run_query(platform.hop_query(1), {"id": 2})
    assert hops[0] == 2  # node 2 is adjacent to 1 and 3

    hops2 = platform.run_query(platform.hop_query(2), {"id": 1})
    assert hops2[0] >= 1  # at depth-2 from node 1 we reach node 3

    hops3 = platform.run_query(platform.hop_query(3), {"id": 1})
    assert hops3[0] >= 0  # depth-3 should not crash

    platform.close()


def test_mock_filtered_lookup(tmp_path: Path):
    nodes = tmp_path / "nodes.csv"
    edges = tmp_path / "edges.csv"
    nodes.write_text("id,community\n10,5\n20,5\n30,9\n", encoding="utf-8")
    edges.write_text("src,dst\n10,20\n", encoding="utf-8")

    platform = MockPlatform()
    platform.connect()
    platform.load_from_csv(nodes, edges)

    results = platform.run_query(platform.filtered_lookup_query(), {"community": 5})
    ids = [r["id"] for r in results]
    assert 10 in ids and 20 in ids
    assert 30 not in ids
    platform.close()


def test_mock_aggregation(tmp_path: Path):
    nodes = tmp_path / "nodes.csv"
    edges = tmp_path / "edges.csv"
    nodes.write_text("id,community\n1,0\n2,0\n3,1\n", encoding="utf-8")
    edges.write_text("src,dst\n1,2\n1,3\n2,3\n", encoding="utf-8")

    platform = MockPlatform()
    platform.connect()
    platform.load_from_csv(nodes, edges)

    results = platform.run_query(platform.aggregation_query(), {})
    assert isinstance(results, list)
    assert len(results) > 0
    platform.close()


def test_mock_write_query(tmp_path: Path):
    import time

    nodes = tmp_path / "nodes.csv"
    edges = tmp_path / "edges.csv"
    nodes.write_text("id,community\n1,0\n", encoding="utf-8")
    edges.write_text("src,dst\n", encoding="utf-8")

    platform = MockPlatform()
    platform.connect()
    platform.load_from_csv(nodes, edges)
    result = platform.run_query(platform.write_query(), {"id": 1, "ts": time.time()})
    assert result == [1]
    platform.close()


def test_mock_sample_start_nodes(tmp_path: Path):
    nodes = tmp_path / "nodes.csv"
    edges = tmp_path / "edges.csv"
    node_rows = "\n".join(f"{i},0" for i in range(1, 201))
    nodes.write_text(f"id,community\n{node_rows}\n", encoding="utf-8")
    edges.write_text("src,dst\n", encoding="utf-8")

    platform = MockPlatform()
    platform.connect()
    platform.load_from_csv(nodes, edges)
    sample = platform.sample_start_nodes(50)
    assert len(sample) == 50
    assert all(isinstance(i, int) for i in sample)
    platform.close()


# ── PlatformResults cold_start_ms ─────────────────────────────────────────────

def test_platform_results_cold_start():
    r = PlatformResults(platform_key="mock", platform_name="Mock")
    assert r.cold_start_ms is None  # default is None, not 0

    r.cold_start_ms = 42.5
    d = r.to_dict()
    assert d["cold_start_ms"] == pytest.approx(42.5)


def test_latency_stats_roundtrip():
    s = LatencyStats(p50_ms=1.5, p95_ms=4.0, mean_ms=2.0, iterations=100, errors=1)
    assert s.errors == 1


# ── Report markdown generation ────────────────────────────────────────────────

_MOCK_RESULTS = {
    "mock": {
        "platform_name": "Mock",
        "cold_start_ms": 15.3,
        "load": {
            "wall_clock_seconds": 1.2,
            "nodes_per_second": 100,
            "relationships_per_second": 200,
            "method": "mock",
        },
        "traversals": {
            "1_hop": {"p50_ms": 1.0, "p95_ms": 2.0, "mean_ms": 1.2, "iterations": 10, "errors": 0},
            "2_hop": {"p50_ms": 3.0, "p95_ms": 4.0, "mean_ms": 3.1, "iterations": 10, "errors": 0},
            "3_hop": {"p50_ms": 8.0, "p95_ms": 12.0, "mean_ms": 9.0, "iterations": 10, "errors": 0},
        },
        "lookups": {
            "point_lookup": {"p50_ms": 0.4, "p95_ms": 0.8, "mean_ms": 0.5, "iterations": 10, "errors": 0},
            "filtered_lookup": {"p50_ms": 1.1, "p95_ms": 2.0, "mean_ms": 1.3, "iterations": 10, "errors": 0},
        },
        "aggregations": {
            "group_by_community": {"p50_ms": 20.0, "p95_ms": 30.0, "mean_ms": 22.0, "iterations": 10, "errors": 0},
        },
        "mixed_workload": {
            "concurrency_1": {
                "queries_per_second": 50.0,
                "duration_seconds": 5,
                "total_queries": 250,
                "errors": 0,
                "concurrency": 1,
            },
        },
        "footprint": {
            "stored_data_size": "3 nodes",
            "memory_usage": "n/a",
            "instance_specs": "mock",
        },
        "caveats": [],
    }
}


def test_report_markdown(tmp_path: Path):
    out = tmp_path / "REPORT.md"
    text = generate_markdown_report(_MOCK_RESULTS, out)
    assert "Traversal Latency" in text
    assert "Mock" in text
    assert "Cold-Start" in text
    assert "15.3" in text  # cold_start_ms value present
    assert out.exists()


def test_report_caveats(tmp_path: Path):
    results_with_caveat = dict(_MOCK_RESULTS)
    results_with_caveat["mock"] = dict(results_with_caveat["mock"])
    results_with_caveat["mock"]["caveats"] = ["Connection timed out at c=40"]
    out = tmp_path / "REPORT.md"
    text = generate_markdown_report(results_with_caveat, out)
    assert "Caveats" in text
    assert "Connection timed out" in text


def test_report_chart_generation(tmp_path: Path):
    """Charts should render without error and produce .png files."""
    from graph_bench.report import generate_charts

    chart_dir = tmp_path / "charts"
    paths = generate_charts(_MOCK_RESULTS, chart_dir)
    # At minimum the traversal and ingest charts should exist
    assert any("ingest" in p.name for p in paths)
    assert all(p.exists() for p in paths)
    assert all(p.suffix == ".png" for p in paths)
