# Five graph databases, one small computer, no victory lap

*A take-home benchmark of CognoDB Cloud against Neo4j Aura, Memgraph, FalkorDB, and ArangoDB — written so a working engineer can rerun it, distrust it, and still learn something.*

The brief from Wexa AI is unusually adult: **do not pick a winner**. Compare managed graph databases the way you would compare compilers — same program, same machine class, published caveats. This repository is that experiment.

If you only remember three things:

1. Every number is a **percentile on a free/entry tier**, not a datacenter shoot-out.
2. CognoDB, Neo4j, and Memgraph speak **Cypher over Bolt**. FalkorDB speaks Cypher over Redis. ArangoDB speaks **AQL**. Language is part of the result.
3. A 3-hop count on 256 MB of RAM is a different sport from a 3-hop count on a paid cluster. We sized the graph so the poorest machine in the lineup can still finish.

---

## Why these five, and not “the top of DB-Engines”

Choosing the field is half the assignment.

**CognoDB Cloud** is the product under evaluation. It advertises a Neo4j-compatible Bolt endpoint. That is a gift for fairness: the same official `neo4j` Python driver, the same Cypher strings, three different runtimes.

**Neo4j Aura Free** is the incumbent. If CognoDB is slower or faster than Aura on identical Cypher, the delta is *product and tenancy*, not “we wrote a worse query for Neo4j.”

**Memgraph** is Cypher/Bolt again, but in-memory and self-hosted. Capping it to 0.5 vCPU / 256 MB in Docker answers a question Aura and CognoDB cannot: *what does the algorithm cost when the network hop is localhost and the working set fits in RAM?*

**FalkorDB** (the RedisGraph line) keeps Cypher-shaped queries on a Redis protocol and adjacency packed into RAM. If 1-hop lookups look similar to Memgraph and 3-hop looks different, you are looking at planner and representation, not “graphs vs documents.”

**ArangoDB** is the control group for query language. The harness translates each logical workload into AQL. If Arango wins aggregations and loses 3-hop, that is a statement about `COLLECT` vs `count(DISTINCT)` — and we say so instead of pretending Cypher was executed.

We did **not** include Amazon Neptune, TigerGraph Cloud, or JanusGraph-as-a-service. Their free tiers are either missing, credit-card gated, or Gremlin/SPARQL-only in a way that would force a second client stack and break “same client machine, same driver style.” That omission is a limitation, not a slight.

---

## The fairness contract

CognoDB’s free **c0** instance is intentionally tiny: burstable **0.5 vCPU, 256 MB RAM, 1 GB disk**. The assignment is explicit: comparing that to a paid Aura instance is a methodology error.

So the contract is:

| Rule | How we implement it |
|------|---------------------|
| Same resources | Docker `cpus: 0.50` and `mem_limit: 256m` for Memgraph, FalkorDB, ArangoDB. Cloud DBs use their **free** tier only. |
| Same data | One `nodes.csv` / `edges.csv` pair, generated once, loaded everywhere. |
| Same queries | Shared templates on the adapter base class. ArangoDB maps them to AQL; it does not invent a friendlier query. |
| Same client | One laptop (or CI runner), one region preference. |
| Warm, then measure | 10 warm-up iterations. Read workloads ≥100 times. Report **p50 and p95**, not a lonely average. |
| Concurrency sweep | Mixed 80/20 read/write at 1, 10, and 40 clients. Throughput *and* error count. |
| Observable vs not | If the console does not expose RSS or on-disk bytes, we print **not observable**. We do not scrape undocumented endpoints. |

If a platform throttles, times out, or rejects a 3-hop because the planner exploded, that row still appears. Failures are data.

---

## The graph

Primary source: Stanford SNAP **soc-Pokec** — the assignment’s named example, a directed Slovak social network. Full dump is ~1.6M nodes / 30M edges; we take the first **150,000** `FRIEND` edges so the graph fits a 256 MB / 1 GB free tier.

Schema on every platform:

```text
(:Person {id, community})-[:FRIEND]->(:Person)
```

`community` is a cheap degree bucket (`(degree // 5) % 10`). It exists so the **filtered lookup** has an indexed property that is not unique. We are not claiming a real Louvain community.

Download order in `prepare`:

1. SNAP soc-Pokec relationships (used if the gz is already local or the download succeeds).
2. SNAP **cit-HepPh** (~1.4 MB) if Pokec cannot be fetched — still a public graph with ≥100k edges, and the assignment lists citation networks as valid.
3. Seeded **Barabási–Albert** (`seed=42`) only if SNAP is fully unreachable. That fact is written into `dataset_metadata.json`. Offline mode is for dry-runs; a submission run should prefer SNAP.

---

## How to read the charts (once you have them)

**Ingest (rels/s).** On Bolt cloud endpoints this is mostly *round trips × batch size × WAN*. Local Docker will look heroic. Do not crown Memgraph “the best database” because `localhost` beat `bolt+s://…cloud`. Compare CognoDB vs Aura first — same WAN class — then look at local engines as an upper bound for the *algorithm*, not the *product*.

**1-hop latency.** Should be index + a few pointer chases. If p95 is tens of milliseconds on a point-neighbour count, you are seeing network, cold page cache, or a missing index. We create `Paper.id` and `Paper.community` indexes on every adapter; if a platform ignores `CREATE INDEX`, the filtered-lookup row will confess.

**2-hop and 3-hop.** Variable-length `MATCH` with `count(DISTINCT)` is where planners and memory models diverge. In-memory engines often keep expanding. Persistent stores may hit the buffer pool. Distinct-count at depth 3 on a social prefix of Pokec is still cheaper than the full 30M-edge graph — which is the point of sampling.

**Point vs filtered lookup.** Point lookup on `id` is the “did you actually use an index” canary. Filtered `community = $x LIMIT 25` is the “is the secondary index real” canary.

**Aggregation.** Top-10 communities by neighbour count. This is closer to an analytic scan than a OLTP ping. Expect it to dominate the latency table. That is useful: it stops us from overfit-tuning 1-hop.

**Mixed QPS at 1 / 10 / 40.** Free tiers often look fine at c=1 and fall over at c=40 (connection caps, burstable CPU, request queues). Plot QPS **and** errors. A platform that holds 200 q/s with 0 errors is healthier than one that spikes 800 q/s with 40% failures.

---

## Why the platforms will differ (even before you run)

You can reason about the shape of the results without cheating:

- **CognoDB vs Neo4j Aura.** Same Cypher, both managed, both far away. Differences here are tenancy, caching, and how aggressively the free tier throttles. This is the comparison the assignment actually cares about.
- **Memgraph vs the two clouds.** Expect lower 1-hop latency (localhost + RAM) and higher mixed QPS until the 200 MB `memory-limit` is hit. If mixed errors climb at c=40, that is the cap working, not a bug in the harness.
- **FalkorDB.** Adjacency in Redis can make shallow hops look excellent. Deeper `*1..3` patterns depend on how complete the Cypher subset is. We try two `CREATE INDEX` dialects and swallow the one that the server rejects.
- **ArangoDB.** `import_bulk` often wins ingest (HTTP bulk vs Cypher `MERGE` per batch). Traversals go through AQL `FOR v IN 1..k ANY`. That is a fair *logical* equivalent and an unfair *optimizer* equivalent. The report must say both sentences.

None of that is a ranking. It is a map of *where to look* when a number surprises you.

---

## What this benchmark is not

- Not TPC. Not LDBC SNB. Those exist; they need bigger machines than c0.
- Not a security audit, not a cost model, not “CognoDB is production-ready.”
- Not vendor-neutral in motivation — it exists because Wexa asked for evangelism-quality explanation. It *is* vendor-neutral in **protocol**: the same scripts, the same CSV, the same percentiles.

If a number in `results/latest.json` makes a database look bad, the first question is: *did we measure the WAN, the burst, or the engine?* The harness records enough metadata to answer that. Use it.

---

## Reproduce it

```bash
pip install -e .
cp .env.example .env          # CognoDB + Aura credentials
docker compose up -d
graph-bench prepare
graph-bench run
graph-bench report
```

Or, to prove the plumbing without accounts:

```bash
graph-bench dry-run
```

Then write your own paragraph under **Analysis** in the README. The interesting submission is not “Memgraph had the lowest p50.” It is “here is why 3-hop p95 on Aura moved and CognoDB’s did not — and here is the caveat that almost fooled us.”

That is the job: explain a deep technical subject and still be believed.
