"""Command-line interface for graph-bench."""

from __future__ import annotations

import os
from pathlib import Path

import click
from rich.console import Console

from graph_bench.config import RESULTS_DIR, selected_platforms
from graph_bench.dataset import prepare_dataset
from graph_bench.report import generate_report
from graph_bench.runner import run_all, run_platform_benchmark

console = Console()


@click.group()
@click.version_option()
def main() -> None:
    """Graph database cloud benchmarking suite."""


@main.command()
@click.option("--force", is_flag=True, help="Re-download and re-sample dataset.")
def prepare(force: bool) -> None:
    """Download and prepare the SNAP soc-Pokec sample (citation-graph fallback)."""
    stats = prepare_dataset(force=force)
    console.print(
        f"[green]Ready:[/green] {stats.node_count:,} nodes, "
        f"{stats.relationship_count:,} relationships"
    )
    console.print(f"  Source: {stats.source}")
    console.print(f"  Nodes: {stats.nodes_file}")
    console.print(f"  Edges: {stats.edges_file}")


@main.command()
@click.option(
    "--platform",
    "-p",
    multiple=True,
    help="Platform key(s) to benchmark. Default: all configured.",
)
@click.option("--skip-load", is_flag=True, help="Skip data load (data already present).")
@click.option("--output", type=click.Path(), default=str(RESULTS_DIR))
def run(platform: tuple[str, ...], skip_load: bool, output: str) -> None:
    """Run the full benchmark suite."""
    from pathlib import Path

    targets = list(platform) if platform else selected_platforms()
    console.print(f"Platforms: {', '.join(targets)}")
    run_all(platforms=targets, skip_load=skip_load, output_dir=Path(output))


@main.command("run-one")
@click.argument("platform_key")
@click.option("--skip-load", is_flag=True)
def run_one(platform_key: str, skip_load: bool) -> None:
    """Benchmark a single platform."""
    from graph_bench.metrics import save_results

    result = run_platform_benchmark(platform_key, skip_load=skip_load)
    out = RESULTS_DIR / f"{platform_key}_latest.json"
    save_results({platform_key: result}, out)
    console.print(f"[green]Saved {out}[/green]")


@main.command("dry-run")
def dry_run() -> None:
    """Exercise the harness against an in-memory mock (no database required)."""
    from pathlib import Path

    os.environ.setdefault("GRAPH_BENCH_OFFLINE", "1")
    os.environ.setdefault("BENCH_ITERATIONS", "20")
    os.environ.setdefault("BENCH_WARMUP", "2")
    os.environ.setdefault("BENCH_CONCURRENCY", "1,4")
    os.environ.setdefault("BENCH_MIXED_SECONDS", "5")
    console.print("[yellow]Dry-run: mock graph, reduced iterations.[/yellow]")
    run_all(platforms=["mock"], skip_load=False, output_dir=RESULTS_DIR)
    generate_report(Path(RESULTS_DIR))
    console.print("[green]Dry-run complete. See results/REPORT.md[/green]")


@main.command()
@click.option("--output", type=click.Path(), default=str(RESULTS_DIR))
def report(output: str) -> None:
    """Generate markdown report and charts from latest results."""
    from pathlib import Path

    path = generate_report(Path(output))
    console.print(f"[green]Report: {path}[/green]")
    console.print(f"[green]Charts: {Path(output) / 'charts'}[/green]")


@main.command()
@click.option("--port", "-p", default=8000, help="Port to host the dashboard on")
def serve(port: int) -> None:
    """Launch the interactive Web Dashboard & Graph Visualizer."""
    import http.server
    import socketserver
    import webbrowser
    import os

    web_dir = Path(__file__).resolve().parent.parent.parent / "web"
    os.chdir(web_dir)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(web_dir), **kwargs)

    socketserver.TCPServer.allow_reuse_address = True
    for p in range(port, port + 20):
        try:
            httpd = socketserver.TCPServer(("", p), Handler)
            url = f"http://localhost:{p}"
            console.print(f"[bold cyan]GraphBench Web Dashboard running at {url}[/bold cyan]")
            console.print("[dim]Press Ctrl+C to stop.[/dim]")
            try:
                webbrowser.open(url)
            except Exception:
                pass
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                console.print("\n[yellow]Shutting down web server.[/yellow]")
            return
        except OSError:
            continue
    console.print(f"[red]Could not bind to any port between {port} and {port+20}[/red]")


if __name__ == "__main__":
    main()
