"""Configuration loading from YAML and environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "platforms.yaml"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = ROOT / "results"


@dataclass
class BenchmarkConfig:
    warmup_iterations: int = 10
    read_iterations: int = 100
    batch_size: int = 1000
    mixed_duration_seconds: int = 60
    concurrency_levels: list[int] = field(default_factory=lambda: [1, 10, 40])
    read_write_ratio: str = "80/20"


@dataclass
class DatasetConfig:
    source: str
    source_url: str
    target_relationships: int
    node_label: str
    relationship_type: str


@dataclass
class PlatformSpec:
    key: str
    name: str
    driver: str
    tier: str
    vcpu: Any
    ram_mb: Any
    storage_gb: Any
    protocol: str
    indexed_properties: list[str]
    notes: str


def load_config() -> dict[str, Any]:
    load_dotenv(ROOT / ".env")
    with CONFIG_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_benchmark_config(cfg: dict[str, Any] | None = None) -> BenchmarkConfig:
    cfg = cfg or load_config()
    bench = cfg.get("benchmark", {})
    env_iters = os.getenv("BENCH_ITERATIONS")
    env_warmup = os.getenv("BENCH_WARMUP")
    env_conc = os.getenv("BENCH_CONCURRENCY")
    return BenchmarkConfig(
        warmup_iterations=int(env_warmup or bench.get("warmup_iterations", 10)),
        read_iterations=int(env_iters or bench.get("read_iterations", 100)),
        batch_size=bench.get("batch_size", 1000),
        mixed_duration_seconds=int(
            os.getenv("BENCH_MIXED_SECONDS") or bench.get("mixed_duration_seconds", 60)
        ),
        concurrency_levels=(
            [int(x) for x in env_conc.split(",")]
            if env_conc
            else bench.get("concurrency_levels", [1, 10, 40])
        ),
        read_write_ratio=bench.get("read_write_ratio", "80/20"),
    )


def get_dataset_config(cfg: dict[str, Any] | None = None) -> DatasetConfig:
    cfg = cfg or load_config()
    ds = cfg["dataset"]
    return DatasetConfig(**ds)


def get_platform_specs(cfg: dict[str, Any] | None = None) -> dict[str, PlatformSpec]:
    cfg = cfg or load_config()
    specs: dict[str, PlatformSpec] = {}
    for key, meta in cfg["platforms"].items():
        specs[key] = PlatformSpec(key=key, **meta)
    return specs


def selected_platforms(cfg: dict[str, Any] | None = None) -> list[str]:
    env = os.getenv("BENCH_PLATFORMS")
    if env:
        return [p.strip() for p in env.split(",") if p.strip()]
    return list(get_platform_specs(cfg).keys())
