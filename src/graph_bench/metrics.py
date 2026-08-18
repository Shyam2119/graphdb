"""Latency and throughput statistics."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np


@dataclass
class LatencyStats:
    p50_ms: float
    p95_ms: float
    mean_ms: float
    iterations: int
    errors: int = 0


@dataclass
class ThroughputStats:
    queries_per_second: float
    duration_seconds: float
    total_queries: int
    errors: int = 0
    concurrency: int = 1


@dataclass
class PlatformResults:
    platform_key: str
    platform_name: str
    load: dict[str, Any] = field(default_factory=dict)
    traversals: dict[str, LatencyStats] = field(default_factory=dict)
    lookups: dict[str, LatencyStats] = field(default_factory=dict)
    aggregations: dict[str, LatencyStats] = field(default_factory=dict)
    mixed_workload: dict[str, ThroughputStats] = field(default_factory=dict)
    footprint: dict[str, Any] = field(default_factory=dict)
    caveats: list[str] = field(default_factory=list)
    # Cold-start: single 1-hop query before warm-up (reflects page-cache cold state)
    cold_start_ms: float | None = None


    def to_dict(self) -> dict[str, Any]:
        def convert(obj: Any) -> Any:
            if isinstance(obj, (LatencyStats, ThroughputStats)):
                return asdict(obj)
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj

        return convert(asdict(self))


def percentile_latencies(samples_ms: list[float]) -> LatencyStats:
    if not samples_ms:
        return LatencyStats(p50_ms=0.0, p95_ms=0.0, mean_ms=0.0, iterations=0)
    arr = np.array(samples_ms, dtype=np.float64)
    return LatencyStats(
        p50_ms=float(np.percentile(arr, 50)),
        p95_ms=float(np.percentile(arr, 95)),
        mean_ms=float(np.mean(arr)),
        iterations=len(samples_ms),
    )


class Timer:
    """Context manager returning elapsed milliseconds."""

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000.0


def save_results(results: dict[str, PlatformResults], path: str | Any) -> None:
    payload = {k: v.to_dict() for k, v in results.items()}
    path = str(path)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
