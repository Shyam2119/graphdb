# Graph Database Cloud Benchmarking & Interactive Explorer Suite

Reproducible comparison of **[CognoDB Cloud](https://cognodb.com)** against four other graph databases on the **same dataset**, **same workloads**, and **same resource envelope**.

Includes a **Full-Stack Interactive Web Dashboard & Physics Graph Visualizer** to explore live multi-hop traversals, benchmark analytics, and query simulations.

> 🌐 **Interactive Web Application**: Run `graph-bench serve` or open [`web/index.html`](web/index.html) to launch the interactive UI dashboard locally or deploy with 1-click to Vercel/Netlify.
>
> 📖 [Read the complete technical write-up →](ARTICLE.md)

## 🌟 Interactive Web Dashboard Features

- 🔮 **Force-Directed Graph Canvas**: Interactive particle physics graph visualization with zoom/pan and node inspection.
- ⚡ **Multi-Hop Traversal Simulator**: Live visual path expansion for 1-hop, 2-hop, and 3-hop graph queries.
- 📊 **Interactive Benchmark Analytics**: Switch between p50/p95 latency curves, concurrency sweeps (c=1, 10, 40), and ingest throughput.
- 💻 **Cypher Query Playground**: Live query evaluator with parameter inputs and execution plan breakdowns.
- ⚖️ **Architectural Matrix**: Compiler-style feature and resource envelope inspector.

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
graph-bench serve               # launch interactive Web UI at http://localhost:8080
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

The numbers below were produced by running the benchmark suite against all 5 databases on the same 150k edge dataset with the same query suites and resource constraints.

### Data loading

| Platform | Load time (s) | Nodes/s | Rels/s | Method |
|---|---|---|---|---|
| **Memgraph** | **9.77** | **7,582** | **15,355** | Neo4j Python driver UNWIND batch MERGE |
| **ArangoDB** | 17.48 | 4,236 | 8,580 | ArangoDB `import_bulk` |
| **FalkorDB** | 24.41 | 3,034 | 6,144 | FalkorDB Cypher UNWIND batch |
| **Neo4j Aura** | 24.47 | 3,027 | 6,130 | Neo4j Python driver UNWIND batch MERGE |
| **CognoDB Cloud** | 80.18 | 924 | 1,871 | Neo4j Python driver UNWIND batch MERGE |

### Traversal latency (p50 / p95 ms)

| Platform | Cold 1-hop | 1-hop (warm) | 2-hop | 3-hop |
|---|---|---|---|---|
| **Memgraph** | 42.0 ms | **2.5 / 4.9 ms** | **4.7 / 16.6 ms** | **86.2 / 401.1 ms** |
| **FalkorDB** | **7.0 ms** | **1.1 / 2.1 ms** | **3.4 / 14.5 ms** | 218.5 / 834.4 ms ⚠ 9 err |
| **Neo4j Aura** | 70.2 ms | 52.1 / 61.0 ms | 52.8 / 58.9 ms | **70.8 / 100.6 ms** |
| **ArangoDB** | 67.3 ms | 50.0 / 62.3 ms | 64.0 / 116.2 ms | 1289.9 / 6629.9 ms |
| **CognoDB Cloud** | 312.4 ms | 252.3 / 259.1 ms | 263.7 / 379.4 ms | 2184.1 / 6306.9 ms ⚠ 77 err |

### Lookups (p50 / p95 ms)

| Platform | Point lookup (`id`) | Filtered lookup (`community`) |
|---|---|---|
| **Memgraph** | **0.9 / 2.3 ms** | **1.5 / 2.4 ms** |
| **FalkorDB** | **1.5 / 3.9 ms** | **1.8 / 9.0 ms** |
| **Neo4j Aura** | 51.3 / 101.1 ms | 102.0 / 163.8 ms |
| **ArangoDB** | 50.1 / 59.5 ms | 50.4 / 61.5 ms |
| **CognoDB Cloud** | 243.9 / 247.9 ms ⚠ 4 err | 246.0 / 469.4 ms |

### Aggregations (p50 / p95 ms)

| Platform | Group-by community (top 10) |
|---|---|
| **Memgraph** | **290.0 / 371.1 ms** |
| **Neo4j Aura** | **306.3 / 364.7 ms** |
| **FalkorDB** | 686.2 / 824.6 ms |
| **ArangoDB** | 1911.7 / 2434.7 ms |
| **CognoDB Cloud** | 2301.1 / 2434.0 ms |

### Mixed workload QPS (80/20 read/write, 60 s sustained)

| Platform | c=1 | c=10 | c=40 (peak) | Errors @ c=40 |
|---|---|---|---|---|
| **Memgraph** | 363.1 q/s | 889.1 q/s | **1,087.1 q/s** | 4 errors |
| **FalkorDB** | **377.4 q/s** | **1,094.5 q/s** | 967.8 q/s | 78 errors |
| **Neo4j Aura** | 12.3 q/s | 167.3 q/s | **607.6 q/s** | **0 errors (100% success)** |
| **ArangoDB** | 19.0 q/s | 180.1 q/s | 397.8 q/s | **0 errors (100% success)** |
| **CognoDB Cloud** | 4.0 q/s | 39.3 q/s | 123.6 q/s | 1,318 errors |

### Footprint & Resource Utilization

| Platform | Stored data size | Memory observation | Notes |
|---|---|---|---|
| **Memgraph** | 74,062 nodes, 150,000 rels | Capped 256 MB (Docker) | In-memory index + adjacency list |
| **FalkorDB** | 74,062 nodes, 150,000 rels | 31.49 MB reported | Redis sparse graph representation |
| **ArangoDB** | 74,062 vertices, 150,000 edges | Docker capped 256 MB | RocksDB storage engine |
| **Neo4j Aura** | 74,062 nodes, 150,000 rels | Managed cloud (~256 MB tier) | Page cache + property store |
| **CognoDB Cloud** | 74,062 nodes, 150,000 rels | Cloud c0 Free (512 MB allocated) | us-east4 cloud instance |

---

## Charts

All charts were automatically generated from `results/latest.json` via `graph-bench report`:

![Traversal Latency by Hop Depth](results/charts/traversal_latency.png)

![Mixed Workload QPS vs Concurrency](results/charts/mixed_workload_qps.png)

![Lookup Latency](results/charts/lookup_latency.png)

![Aggregation Latency](results/charts/aggregation_latency.png)

![Ingest Throughput](results/charts/ingest_throughput.png)

---

## Engineering Analysis & Findings

### 1. In-Memory Local vs. Cloud Network Boundaries
- **Memgraph** and **FalkorDB** demonstrated sub-3 ms latency on 1-hop traversals and point lookups due to in-memory architectures and zero-network overhead on localhost.
- **Neo4j Aura** and **CognoDB Cloud** both include WAN transport overhead. Neo4j Aura maintained a consistent ~50 ms baseline across lookups and shallow hops, scaling gracefully to **607.6 QPS at c=40 with zero errors**.
- **CognoDB Cloud** was measured against its live `us-east4` endpoint from the client network, showing a ~240 ms round-trip transport floor.

### 2. Multi-Hop Path Expansion (3-Hop Traversal)
- Deep traversals (`3-hop distinct`) test graph pointer-chasing and query planner pruning:
  - **Neo4j Aura** had the most consistent deep-traversal plan: only **70.8 ms p50** at 3 hops, scaling with minimal penalty due to Cypher's path caching.
  - **Memgraph** executed 3-hops in **86.2 ms p50**, showing rapid in-memory expansion.
  - **ArangoDB** and **CognoDB** experienced exponential expansion execution times (~1.2s to 2.1s p50) on dense subgraphs.

### 3. Concurrency Scaling & Stability under Load (c=1, 10, 40)
- **Zero-Error Tier**: **Neo4j Aura** (0 errors across all concurrency tiers up to 607 QPS) and **ArangoDB** (0 errors at c=40).
- **In-Memory Saturation**: **Memgraph** scaled smoothly to **1,087 QPS** with minimal socket retries (4 errors). **FalkorDB** peaked at **1,094 QPS** at c=10, before hitting Redis connection queue contention at c=40 (78 errors).
- **CognoDB Free (c0)**: Scaled from 4 QPS (c=1) to 39.3 QPS (c=10) with 0 errors. Under saturated c=40 concurrent threads, the c0 instance connection pool reached its limit, resulting in connection resets and timeouts, identifying the burstable tier's concurrency ceiling.

### 4. Aggregations & Graph Analytics
- Full-graph community group-by aggregations (`MATCH (n)-[:FRIEND]-(m) RETURN n.community, count(m)`) highlighted query planner optimizations:
  - **Memgraph** (290 ms) and **Neo4j** (306 ms) were the top performers for topological aggregation.
  - **FalkorDB** followed at 686 ms.
  - **ArangoDB** (1,911 ms) and **CognoDB** (2,301 ms) reflect scan-heavy collection aggregations.

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

## Live Web Application

- **Production URL**: [https://shyam2119.github.io/graphdb/](https://shyam2119.github.io/graphdb/)
- **Local Runner**: `graph-bench serve` (launches at `http://localhost:8000`)

## Author

**Shyam Pattipu** — [GitHub Profile](https://github.com/Shyam2119)

## License

MIT. SNAP data remains under SNAP’s terms; we only redistribute sampled CSVs generated locally.
