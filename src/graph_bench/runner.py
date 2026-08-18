"""Benchmark orchestration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from graph_bench.config import RESULTS_DIR, get_benchmark_config, get_platform_specs
from graph_bench.dataset import prepare_dataset
from graph_bench.metrics import PlatformResults, Timer, save_results
from graph_bench.platforms import create_platform
from graph_bench.workloads import (
    run_aggregation_benchmark,
    run_lookup_benchmark,
    run_mixed_workload,
    run_traversal_benchmark,
    warmup,
)

console = Console()


def _load_communities(nodes_file: Path) -> list[int]:
    import csv

    communities: set[int] = set()
    with nodes_file.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            communities.add(int(row["community"]))
    return list(communities)


def run_platform_benchmark(
    platform_key: str,
    skip_load: bool = False,
) -> PlatformResults:
    cfg = get_benchmark_config()
    dataset = prepare_dataset()
    if platform_key == "mock":
        platform_name = "Mock (dry-run)"
        platform = create_platform("mock", batch_size=cfg.batch_size)
    else:
        spec = get_platform_specs()[platform_key]
        platform_name = spec.name
        platform = create_platform(platform_key, batch_size=cfg.batch_size)
    result = PlatformResults(platform_key=platform_key, platform_name=platform_name)

    console.print(f"\n[bold cyan]=== {platform_name} ({platform_key}) ===[/bold cyan]")

    try:
        platform.connect()
    except Exception as exc:
        result.caveats.append(f"Connection failed: {exc}")
        console.print(f"[red]Connection failed: {exc}[/red]")
        return result

    try:
        if not skip_load:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as prog:
                task = prog.add_task("Loading dataset...", total=None)
                load_metrics = platform.load_from_csv(dataset.nodes_file, dataset.edges_file)
                prog.remove_task(task)
            result.load = {
                "wall_clock_seconds": round(load_metrics.wall_clock_seconds, 2),
                "nodes_loaded": load_metrics.nodes_loaded,
                "relationships_loaded": load_metrics.relationships_loaded,
                "nodes_per_second": round(load_metrics.nodes_per_second, 1),
                "relationships_per_second": round(load_metrics.relationships_per_second, 1),
                "method": load_metrics.method,
            }
            console.print(
                f"  Loaded {load_metrics.relationships_loaded:,} rels in "
                f"{load_metrics.wall_clock_seconds:.1f}s "
                f"({load_metrics.relationships_per_second:,.0f} rel/s)"
            )
        else:
            result.caveats.append("Data load skipped (--skip-load)")

        start_nodes = platform.sample_start_nodes(min(500, dataset.node_count))
        communities = _load_communities(dataset.nodes_file)

        # --- Cold-start measurement ---
        # One timed query immediately after connect / load, before any warm-up.
        # This is the number that reflects page-cache cold state.
        if start_nodes:
            with Timer() as cold_t:
                try:
                    platform.run_query(platform.hop_query(1), {"id": start_nodes[0]})
                except Exception:
                    pass
            result.cold_start_ms = round(cold_t.elapsed_ms, 2)
            console.print(f"  Cold-start 1-hop: {result.cold_start_ms:.1f} ms")

        console.print("  Warming up...")
        warmup(platform, start_nodes, cfg)

        console.print("  Running traversal benchmarks...")
        result.traversals = run_traversal_benchmark(platform, start_nodes, cfg)

        console.print("  Running lookup benchmarks...")
        result.lookups = run_lookup_benchmark(platform, start_nodes, communities, cfg)

        console.print("  Running aggregation benchmark...")
        result.aggregations = run_aggregation_benchmark(platform, cfg)

        console.print("  Running mixed workload (concurrency sweep)...")
        for conc in cfg.concurrency_levels:
            stats = run_mixed_workload(platform, start_nodes, cfg, conc)
            result.mixed_workload[f"concurrency_{conc}"] = stats
            console.print(
                f"    concurrency={conc}: {stats.queries_per_second:.1f} q/s "
                f"({stats.errors} errors)"
            )

        footprint = platform.get_footprint()
        result.footprint = {
            "stored_data_size": footprint.stored_data_size,
            "memory_usage": footprint.memory_usage,
            "instance_specs": footprint.instance_specs,
            "notes": footprint.notes,
        }

    except Exception as exc:
        result.caveats.append(f"Benchmark error: {exc}")
        console.print(f"[red]Benchmark error: {exc}[/red]")
    finally:
        platform.close()

    return result


def run_all(
    platforms: list[str] | None = None,
    skip_load: bool = False,
    output_dir: Path | None = None,
) -> dict[str, PlatformResults]:
    output_dir = output_dir or RESULTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    prepare_dataset()
    targets = platforms or list(get_platform_specs().keys())
    all_results: dict[str, PlatformResults] = {}

    for key in targets:
        all_results[key] = run_platform_benchmark(key, skip_load=skip_load)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_file = output_dir / f"benchmark_{ts}.json"
    save_results(all_results, out_file)
    console.print(f"\n[green]Results saved to {out_file}[/green]")

    # Also write latest symlink-style copy
    latest = output_dir / "latest.json"
    save_results(all_results, latest)

    meta: dict[str, Any] = {
        "timestamp_utc": ts,
        "platforms": targets,
    }
    meta_path = Path(__file__).resolve().parents[2] / "data" / "processed" / "dataset_metadata.json"
    if meta_path.exists():
        try:
            meta["dataset"] = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta["dataset"] = "unavailable"
    else:
        meta["dataset"] = "not yet prepared (run `graph-bench prepare` first)"
    (output_dir / "run_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return all_results
