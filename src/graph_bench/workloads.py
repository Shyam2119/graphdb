"""Benchmark workload execution."""

from __future__ import annotations

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from graph_bench.config import BenchmarkConfig
from graph_bench.metrics import LatencyStats, ThroughputStats, Timer, percentile_latencies
from graph_bench.platforms.base import GraphPlatform


def _run_timed(platform: GraphPlatform, query: str, params: dict[str, Any]) -> tuple[float | None, str | None]:
    try:
        with Timer() as t:
            platform.run_query(query, params)
        return t.elapsed_ms, None
    except Exception as exc:
        return None, str(exc)


def warmup(platform: GraphPlatform, start_nodes: list[int], cfg: BenchmarkConfig) -> None:
    if not start_nodes:
        return
    for _ in range(cfg.warmup_iterations):
        nid = random.choice(start_nodes)
        try:
            platform.run_query(platform.hop_query(1), {"id": nid})
        except Exception:
            continue


def run_traversal_benchmark(
    platform: GraphPlatform,
    start_nodes: list[int],
    cfg: BenchmarkConfig,
) -> dict[str, LatencyStats]:
    results: dict[str, LatencyStats] = {}
    for depth in (1, 2, 3):
        query = platform.hop_query(depth)
        samples: list[float] = []
        errors = 0
        for _ in range(cfg.read_iterations):
            nid = random.choice(start_nodes)
            ms, _err = _run_timed(platform, query, {"id": nid})
            if ms is None:
                errors += 1
            else:
                samples.append(ms)
        stats = percentile_latencies(samples)
        stats.errors = errors
        results[f"{depth}_hop"] = stats
    return results


def run_lookup_benchmark(
    platform: GraphPlatform,
    start_nodes: list[int],
    communities: list[int],
    cfg: BenchmarkConfig,
) -> dict[str, LatencyStats]:
    results: dict[str, LatencyStats] = {}

    point_samples: list[float] = []
    point_errors = 0
    for _ in range(cfg.read_iterations):
        nid = random.choice(start_nodes)
        ms, _err = _run_timed(platform, platform.point_lookup_query(), {"id": nid})
        if ms is None:
            point_errors += 1
        else:
            point_samples.append(ms)
    point_stats = percentile_latencies(point_samples)
    point_stats.errors = point_errors
    results["point_lookup"] = point_stats

    filtered_samples: list[float] = []
    filtered_errors = 0
    pool = communities or [0]
    for _ in range(cfg.read_iterations):
        comm = random.choice(pool)
        ms, _err = _run_timed(platform, platform.filtered_lookup_query(), {"community": comm})
        if ms is None:
            filtered_errors += 1
        else:
            filtered_samples.append(ms)
    filt_stats = percentile_latencies(filtered_samples)
    filt_stats.errors = filtered_errors
    results["filtered_lookup"] = filt_stats

    return results


def run_aggregation_benchmark(
    platform: GraphPlatform,
    cfg: BenchmarkConfig,
) -> dict[str, LatencyStats]:
    samples: list[float] = []
    errors = 0
    for _ in range(cfg.read_iterations):
        ms, _err = _run_timed(platform, platform.aggregation_query(), {})
        if ms is None:
            errors += 1
        else:
            samples.append(ms)
    stats = percentile_latencies(samples)
    stats.errors = errors
    return {"group_by_community": stats}


def run_mixed_workload(
    platform: GraphPlatform,
    start_nodes: list[int],
    cfg: BenchmarkConfig,
    concurrency: int,
) -> ThroughputStats:
    """Sustained read/write mix at fixed concurrency for configured duration."""
    read_pct = 0.8
    if "/" in cfg.read_write_ratio:
        r, w = cfg.read_write_ratio.split("/")
        total_rw = int(r) + int(w)
        read_pct = int(r) / total_rw

    stop_at = time.perf_counter() + cfg.mixed_duration_seconds
    total = 0
    errors = 0
    lock = threading.Lock()

    def one_query() -> bool:
        try:
            nid = random.choice(start_nodes)
            if random.random() < read_pct:
                platform.run_query(platform.read_query(), {"id": nid})
            else:
                platform.run_query(platform.write_query(), {"id": nid, "ts": time.time()})
            return True
        except Exception:
            return False

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        futures: set = set()
        while time.perf_counter() < stop_at:
            while len(futures) < concurrency and time.perf_counter() < stop_at:
                futures.add(pool.submit(one_query))
            done = {f for f in futures if f.done()}
            for fut in done:
                futures.discard(fut)
                with lock:
                    total += 1
                    if not fut.result():
                        errors += 1
            if not done:
                time.sleep(0.001)

        for fut in as_completed(futures):
            with lock:
                total += 1
                if not fut.result():
                    errors += 1

    duration = cfg.mixed_duration_seconds
    return ThroughputStats(
        queries_per_second=total / duration if duration else 0.0,
        duration_seconds=duration,
        total_queries=total,
        errors=errors,
        concurrency=concurrency,
    )
