"""Download and prepare a public citation graph sized for free-tier databases."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from graph_bench.config import PROCESSED_DIR, RAW_DIR, get_dataset_config

# Prefer the local Pokec dump if present (assignment's named example).
# cit-HepPh is the small-download fallback (~1.4 MB).
SNAP_SOURCES = [
    {
        "name": "SNAP Stanford soc-Pokec (sampled)",
        "url": "https://snap.stanford.edu/data/soc-Pokec.html",
        "file_url": "https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz",
        "filename": "soc-Pokec-relationships.txt.gz",
    },
    {
        "name": "SNAP Stanford cit-HepPh (sampled)",
        "url": "https://snap.stanford.edu/data/cit-HepPh.html",
        "file_url": "https://snap.stanford.edu/data/cit-HepPh.txt.gz",
        "filename": "cit-HepPh.txt.gz",
    },
    {
        "name": "SNAP Stanford cit-HepTh (sampled)",
        "url": "https://snap.stanford.edu/data/cit-HepTh.html",
        "file_url": "https://snap.stanford.edu/data/cit-HepTh.txt.gz",
        "filename": "cit-HepTh.txt.gz",
    },
]


@dataclass
class DatasetStats:
    node_count: int
    relationship_count: int
    source: str
    source_url: str
    nodes_file: Path
    edges_file: Path
    metadata_file: Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, dest: Path, timeout: int = 90) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    print(f"Downloading {url} ...")
    req = Request(url, headers={"User-Agent": "graph-bench/1.0 (research benchmark)"})
    with urlopen(req, timeout=timeout) as resp, dest.open("wb") as out:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            out.write(chunk)
    return dest


def _parse_edge_file(path: Path, target_rels: int) -> tuple[list[tuple[int, int]], set[int], dict[int, int]]:
    opener = gzip.open if path.suffix == ".gz" else open
    seen_nodes: set[int] = set()
    degree: dict[int, int] = defaultdict(int)
    sampled_edges: list[tuple[int, int]] = []
    with opener(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.replace(",", " ").split()
            if len(parts) < 2:
                continue
            try:
                src, dst = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            if src == dst:
                continue
            sampled_edges.append((src, dst))
            seen_nodes.add(src)
            seen_nodes.add(dst)
            degree[src] += 1
            degree[dst] += 1
            if len(sampled_edges) >= target_rels:
                break
    return sampled_edges, seen_nodes, degree


def _barabasi_albert(n_nodes: int, n_edges: int, seed: int = 42) -> tuple[list[tuple[int, int]], set[int], dict[int, int]]:
    """Seeded preferential-attachment graph used only if SNAP is unreachable."""
    rng = random.Random(seed)
    m0 = max(3, n_edges // n_nodes)
    nodes = list(range(n_nodes))
    edges: list[tuple[int, int]] = []
    degree: dict[int, int] = defaultdict(int)
    # Start with a small clique so every node has a chance to be cited.
    for i in range(m0):
        for j in range(i + 1, m0):
            edges.append((i, j))
            degree[i] += 1
            degree[j] += 1
    stubs = [i for i, d in degree.items() for _ in range(d)]
    for src in range(m0, n_nodes):
        targets = set()
        while len(targets) < m0 and stubs:
            targets.add(rng.choice(stubs))
        for dst in targets:
            edges.append((src, dst))
            degree[src] += 1
            degree[dst] += 1
            stubs.extend([src, dst])
        if len(edges) >= n_edges:
            break
    while len(edges) < n_edges:
        src, dst = rng.randrange(n_nodes), rng.randrange(n_nodes)
        if src != dst:
            edges.append((src, dst))
            degree[src] += 1
            degree[dst] += 1
    edges = edges[:n_edges]
    seen = set()
    for s, d in edges:
        seen.add(s)
        seen.add(d)
    return edges, seen, degree


def _write_csv(
    nodes_csv: Path,
    edges_csv: Path,
    sampled_edges: list[tuple[int, int]],
    seen_nodes: set[int],
    degree: dict[int, int],
) -> None:
    sorted_nodes = sorted(seen_nodes)
    communities = {nid: (degree.get(nid, 0) // 5) % 10 for nid in sorted_nodes}
    with nodes_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "community"])
        for nid in sorted_nodes:
            writer.writerow([nid, communities[nid]])
    with edges_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["src", "dst"])
        writer.writerows(sampled_edges)


def prepare_dataset(force: bool = False) -> DatasetStats:
    """Prepare ≥100k CITES relationships. Prefers SNAP; falls back if SNAP is down."""
    ds_cfg = get_dataset_config()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    nodes_csv = PROCESSED_DIR / "nodes.csv"
    edges_csv = PROCESSED_DIR / "edges.csv"
    meta_json = PROCESSED_DIR / "dataset_metadata.json"

    if nodes_csv.exists() and edges_csv.exists() and meta_json.exists() and not force:
        meta = json.loads(meta_json.read_text(encoding="utf-8"))
        return DatasetStats(
            node_count=meta["node_count"],
            relationship_count=meta["relationship_count"],
            source=meta["source"],
            source_url=meta["source_url"],
            nodes_file=nodes_csv,
            edges_file=edges_csv,
            metadata_file=meta_json,
        )

    target_rels = ds_cfg.target_relationships
    sampled_edges: list[tuple[int, int]] = []
    seen_nodes: set[int] = set()
    degree: dict[int, int] = defaultdict(int)
    source_name = ds_cfg.source
    source_url = ds_cfg.source_url
    file_sha = ""
    origin = "unknown"

    if os.getenv("GRAPH_BENCH_OFFLINE") == "1":
        print("GRAPH_BENCH_OFFLINE=1 — generating seeded Barabási–Albert graph")
        n_nodes = max(20_000, target_rels // 6)
        sampled_edges, seen_nodes, degree = _barabasi_albert(n_nodes, target_rels, seed=42)
        source_name = "Synthetic Barabási–Albert (seed=42; offline mode)"
        source_url = "https://en.wikipedia.org/wiki/Barab%C3%A1si%E2%80%93Albert_model"
        origin = "local_generator"
        file_sha = "seed=42"
    else:
        for src in SNAP_SOURCES:
            dest = RAW_DIR / src["filename"]
            try:
                _download(src["file_url"], dest)
                sampled_edges, seen_nodes, degree = _parse_edge_file(dest, target_rels)
                if len(sampled_edges) >= 100_000:
                    source_name = src["name"]
                    source_url = src["url"]
                    file_sha = _sha256(dest)
                    origin = src["file_url"]
                    print(f"Using {src['name']}: {len(sampled_edges):,} edges")
                    break
                print(f"{src['name']} only yielded {len(sampled_edges)} edges; trying next source")
            except (URLError, TimeoutError, OSError, ValueError) as exc:
                print(f"Could not use {src['file_url']}: {exc}")
                continue

    if len(sampled_edges) < 100_000:
        print("SNAP unreachable or too small — generating seeded Barabási–Albert graph")
        n_nodes = max(20_000, target_rels // 6)
        sampled_edges, seen_nodes, degree = _barabasi_albert(n_nodes, target_rels, seed=42)
        source_name = "Synthetic Barabási–Albert (seed=42; SNAP fallback)"
        source_url = "https://en.wikipedia.org/wiki/Barab%C3%A1si%E2%80%93Albert_model"
        origin = "local_generator"
        file_sha = "seed=42"

    _write_csv(nodes_csv, edges_csv, sampled_edges, seen_nodes, degree)

    meta = {
        "source": source_name,
        "source_url": source_url,
        "origin_file": origin,
        "node_count": len(seen_nodes),
        "relationship_count": len(sampled_edges),
        "file_sha256": file_sha,
        "node_label": ds_cfg.node_label,
        "relationship_type": ds_cfg.relationship_type,
    }
    meta_json.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(
        f"Prepared dataset: {meta['node_count']:,} nodes, "
        f"{meta['relationship_count']:,} relationships"
    )
    return DatasetStats(
        node_count=meta["node_count"],
        relationship_count=meta["relationship_count"],
        source=meta["source"],
        source_url=meta["source_url"],
        nodes_file=nodes_csv,
        edges_file=edges_csv,
        metadata_file=meta_json,
    )
