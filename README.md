# Graph Database Cloud Benchmarking

Reproducible comparison of **[CognoDB Cloud](https://cognodb.com)** against four other graph databases on the **same dataset**, **same workloads**, and **same resource envelope**.

This is an honest methodology repo — not a leaderboard. The assignment is to measure fairly and explain the numbers. [Read the full write-up →](ARTICLE.md)

## What this suite measures

| Category | Metric | How it is reported |
|----------|--------|--------------------|
| Data loading | Ingest throughput | Nodes/s, relationships/s, wall-clock |
| Cold-start | First 1-hop before warm-up | Single timing; reflects page-cache cold state |
| Traversals | 1-hop, 2-hop, 3-hop | p50 and p95 latency (ms), ≥100 iterations after warm-up |
| Lookups | Point + indexed/filtered | p50 / p95; indexes on `Person.id` and `Person.community` |
| Aggregations | Group-by community | p50 / p95 |
| Mixed workload | Concurrent read/write | QPS at 1 / 10 / 40 concurrent clients, 80/20 read/write mix |
| Footprint | Resource usage | Stored size, memory if exposed, else "not observable" |

## Platforms (why these five)

| Platform | Why it is here | Tier used | vCPU | RAM | Storage |
|----------|----------------|-----------|------|-----|---------|
| **CognoDB Cloud** | Subject of the assignment; Neo4j-compatible Bolt | c0 Free | 0.5 (burstable) | 256 MB | 1 GB |
| **Neo4j Aura** | Incumbent managed Cypher store — same language, different product | AuraDB Free | shared | ~256 MB | caps apply |
| **Memgraph** | In-memory Cypher/Bolt engine — isolates persistence vs RAM | Docker capped | 0.5 | 256 MB | 1 GB |
| **FalkorDB** | Redis-native graph (Cypher subset) — different storage engine | Docker capped | 0.5 | 256 MB | 1 GB |
| **ArangoDB** | Multi-model AQL — query-language contrast, same logical queries | Docker capped | 0.5 | 256 MB | 1 GB |

Three platforms share Cypher+Bolt (CognoDB, Neo4j, Memgraph). Two change the engine (FalkorDB) or the language (ArangoDB). That split is deliberate: it tells you whether a gap is “this cloud” vs “this query model.”

Self-hosted databases are **cgroup-capped** in `docker-compose.yml` to CognoDB’s advertised c0 envelope. Comparing a free cloud instance to an uncapped laptop Docker is a methodology error; we do not do that.

## Dataset

| Field | Value |
|-------|-------|
| Primary source | [SNAP soc-Pokec](https://snap.stanford.edu/data/soc-Pokec.html) (sampled; assignment's named example) |
| Fallback source | [SNAP cit-HepPh](https://snap.stanford.edu/data/cit-HepPh.html) if Pokec cannot be downloaded |
| Target size | 150,000 `FRIEND` relationships (fits 256 MB / 1 GB tiers) |
| Schema | `(:Person {id, community})-[:FRIEND]->(:Person)` |
| Indexes | `Person.id` (unique), `Person.community` (secondary) on every platform |
| Fallback | If SNAP is unreachable: seeded Barabási–Albert graph (`seed=42`), documented in `dataset_metadata.json` |

The assignment asked for a public graph with ≥100k relationships and named a SNAP soc-Pokec sample as an example. We take the first 150,000 edges so the graph fits the smallest free tier. If SNAP Pokec is unreachable, `prepare` tries the smaller cit-HepPh citation network, then a seeded Barabási–Albert graph, and records which origin was used in `dataset_metadata.json`.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -e .

copy .env.example .env          # then fill CognoDB / Neo4j credentials
docker compose up -d            # Memgraph, FalkorDB, ArangoDB (capped)

graph-bench prepare             # download / sample the dataset
graph-bench run                 # load + warm-up + all workloads
graph-bench report              # results/REPORT.md + charts
```

No credentials yet? Validate the harness:

```bash
graph-bench dry-run
```

### One platform at a time

```bash
graph-bench run -p cognodb
graph-bench run-one neo4j
```

Secrets are read from environment variables only. **Never commit `.env`.**

## Results matrix

Numbers below are produced by `graph-bench report` after a real run. Until then the cells stay empty on purpose — filling them with invented latency would be the opposite of this assignment.

After you run, open `results/REPORT.md` and `results/charts/`.

### Data loading

| Platform | Load time (s) | Nodes/s | Rels/s | Method |
|----------|---------------|---------|--------|--------|
| CognoDB Cloud | *run locally* | | | Neo4j driver UNWIND batch |
| Neo4j Aura | *run locally* | | | Neo4j driver UNWIND batch |
| Memgraph | *run locally* | | | Neo4j driver UNWIND batch |
| FalkorDB | *run locally* | | | FalkorDB Cypher UNWIND batch |
| ArangoDB | *run locally* | | | ArangoDB `import_bulk` |

### Traversal latency (p50 / p95 ms)

| Platform | 1-hop | 2-hop | 3-hop |
|----------|-------|-------|-------|
| CognoDB Cloud | | | |
| Neo4j Aura | | | |
| Memgraph | | | |
| FalkorDB | | | |
| ArangoDB | | | |

### Lookups (p50 / p95 ms)

| Platform | Point lookup (`id`) | Filtered lookup (`community`) |
|----------|---------------------|-------------------------------|
| CognoDB Cloud | | |
| Neo4j Aura | | |
| Memgraph | | |
| FalkorDB | | |
| ArangoDB | | |

### Aggregations (p50 / p95 ms)

| Platform | Group-by community |
|----------|--------------------|
| CognoDB Cloud | |
| Neo4j Aura | |
| Memgraph | |
| FalkorDB | |
| ArangoDB | |

### Mixed workload QPS (80/20 read/write, 60 s)

| Platform | c=1 | c=10 | c=40 | Errors |
|----------|-----|------|------|--------|
| CognoDB Cloud | | | | |
| Neo4j Aura | | | | |
| Memgraph | | | | |
| FalkorDB | | | | |
| ArangoDB | | | | |

### Footprint

Record whatever the platform exposes. Where the console does not show RAM or on-disk size, the report writes **not observable** rather than guessing.

## Methodology (short)

1. Same CSV files (`nodes.csv`, `edges.csv`) loaded into every database.
2. Same logical queries: 1/2/3-hop traversal, point lookup, filtered lookup, group-by aggregation, mixed 80/20 R/W.
3. **Cold-start**: one 1-hop query immediately after data load, before any warm-up. Reflects page-cache cold state.
4. **Warm-up**: 10 iterations discarded. Timed workload: ≥100 iterations per read query.
5. **Mixed workload**: 60-second sustained run at concurrency 1 / 10 / 40.
6. Client machine and region fixed throughout. Cloud URIs in a region near the client.
7. Percentiles (p50, p95), not just averages. Error counts are first-class, not hidden.
8. All caveats recorded in `results/latest.json` and surfaced in `results/REPORT.md`.

Full platform selection argument and how to read a free-tier chart: **[ARTICLE.md](ARTICLE.md)**.

## Charts

Generated by `graph-bench report` into `results/charts/`. Committed to the repo after a real run.

| Chart | What it shows |
|-------|---------------|
| `traversal_latency.png` | p50 / p95 for 1-hop, 2-hop, 3-hop per platform |
| `lookup_latency.png` | Point vs filtered lookup |
| `aggregation_latency.png` | Group-by community |
| `ingest_throughput.png` | Relationships ingested per second |
| `mixed_workload_qps.png` | QPS and error count vs concurrency |

## Analysis

*This section is completed after the benchmark run with real numbers.*

Key questions the numbers will answer:

- Does CognoDB's Bolt compatibility translate to Neo4j-comparable latency, or does the c0 free tier throttle significantly?
- Is the latency gap between cloud DBs (CognoDB/Aura) and localhost DBs (Memgraph/FalkorDB) explained by WAN RTT alone?
- Where does AQL (`COLLECT`) vs Cypher (`count(DISTINCT)`) diverge at 3-hop depth and in aggregations?
- At which concurrency level do free tiers start returning errors?


## Project layout

```
.github/workflows/ci.yml   # lint + test on every push (Python 3.10/3.11/3.12)
config/platforms.yaml      # specs, dataset size, iteration counts
docker-compose.yml         # Memgraph / FalkorDB / ArangoDB with 0.5 vCPU / 256 MB
scripts/
  run_benchmark.py         # convenience entry point
  inject_results.py        # merge per-platform JSON results into latest.json
src/graph_bench/
  cli.py                   # graph-bench prepare | run | run-one | report | dry-run
  config.py                # YAML + env loading
  metrics.py               # LatencyStats, ThroughputStats, PlatformResults
  dataset/prepare.py       # SNAP download + sampling (BA fallback)
  platforms/
    base.py                # GraphPlatform ABC
    neo4j.py               # CognoDB, Neo4j Aura, Memgraph (shared Bolt adapter)
    falkordb.py            # FalkorDB (Redis protocol)
    arangodb.py            # ArangoDB (AQL, HTTP)
    mock.py                # In-memory mock (dry-run / tests)
  workloads.py             # traversal, lookup, aggregation, mixed R/W
  runner.py                # orchestration, cold-start measurement
  report.py                # Markdown tables + 5 matplotlib charts
tests/
  test_harness.py          # 17 tests; no live database required
  test_dataset.py          # dataset prep + ArangoDB translation tests
```

## Environment

| Variable | Purpose |
|----------|---------|
| `COGNODB_URI` / `USER` / `PASSWORD` | CognoDB Cloud (`bolt+s://…`) |
| `NEO4J_URI` / `USER` / `PASSWORD` | Neo4j Aura Free |
| `MEMGRAPH_URI` | default `bolt://localhost:7687` |
| `FALKORDB_HOST` / `PORT` | default localhost:6379 |
| `ARANGO_URL` / `USER` / `PASSWORD` | default localhost:8529 |
| `BENCH_ITERATIONS` | read-workload iterations (default 100) |
| `BENCH_WARMUP` | warm-up iterations (default 10) |
| `BENCH_CONCURRENCY` | e.g. `1,10,40` |
| `BENCH_MIXED_SECONDS` | mixed-workload duration (default 60) |
| `BENCH_PLATFORMS` | subset, e.g. `cognodb,memgraph` |
| `GRAPH_BENCH_OFFLINE=1` | skip SNAP; generate seeded BA graph |

## CognoDB Cloud setup

1. Sign up at [console.cognodb.com/signup](https://console.cognodb.com/signup) (no credit card).
2. Create a free **c0** instance in a region close to the machine that will run this repo.
3. Copy the `bolt+s://<id>.databases.cognodb.cloud` URI and the one-time password.
4. Put them in `.env`. The official Neo4j Python driver is the client — no proprietary SDK.

## Honest caveats (expected, not hidden)

- **Network vs engine.** Cloud Bolt endpoints include WAN RTT; Docker on localhost does not. Load times especially will reflect that. Keep the client machine constant and say so.
- **Burstable CPU.** CognoDB c0 is 0.5 vCPU burstable. A short benchmark can look faster than a long one if it rides the burst.
- **Aura Free caps.** Neo4j Aura Free enforces node/relationship limits. If ingest fails, that is a tier limit, recorded in `caveats`, not a silent skip.
- **AQL is not Cypher.** ArangoDB runs equivalent traversals, not the same planner. That is a feature of the comparison, documented in the adapter.
- **Variable-length paths.** 3-hop `DISTINCT` counts are the most planner-sensitive query. Timeouts are reported as errors, not dropped.
- **Do not commit secrets.** Connection URIs and passwords stay in `.env`.

## Tests

```bash
pip install pytest
pytest -q
```

## Submit

1. Push this repo to GitHub (public, or private with access for Wexa).
2. Email **hr@wexa.ai** with subject `CognoDB Assignment 1 – <Your Name>` and the repository URL.

## License

MIT. SNAP data remains under SNAP’s terms; we only redistribute sampled CSVs you generate locally.
