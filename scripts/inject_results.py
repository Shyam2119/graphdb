#!/usr/bin/env python3
"""
inject_results.py — merge per-platform JSON results into results/latest.json.

Usage
-----
After running each platform individually:

    graph-bench run-one memgraph
    graph-bench run-one falkordb
    graph-bench run-one arangodb
    graph-bench run-one neo4j

Each produces results/<platform>_latest.json.  Run this script to merge them:

    python scripts/inject_results.py

The merged file is written to results/latest.json, which `graph-bench report`
reads to generate tables and charts.

You can also inject a single platform into an existing merged file:

    python scripts/inject_results.py --platform neo4j
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge per-platform results into latest.json")
    parser.add_argument(
        "--platform",
        nargs="*",
        help="Platform key(s) to merge. Default: all *_latest.json files found.",
    )
    parser.add_argument(
        "--output",
        default=str(RESULTS_DIR / "latest.json"),
        help="Output path (default: results/latest.json)",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    merged = load_json(output_path)

    if args.platform:
        sources = [RESULTS_DIR / f"{p}_latest.json" for p in args.platform]
    else:
        sources = sorted(RESULTS_DIR.glob("*_latest.json"))

    if not sources:
        print("No per-platform result files found. Run `graph-bench run-one <platform>` first.")
        sys.exit(1)

    injected = 0
    for src in sources:
        if not src.exists():
            print(f"  SKIP {src.name} — file not found")
            continue
        data = load_json(src)
        for key, result in data.items():
            merged[key] = result
            print(f"  MERGED {key} from {src.name}")
            injected += 1

    if injected == 0:
        print("Nothing to merge.")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"\nWrote {injected} platform(s) to {output_path}")
    print("Run `graph-bench report` to generate REPORT.md and charts.")


if __name__ == "__main__":
    main()
