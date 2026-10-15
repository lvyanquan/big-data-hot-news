# Editorial and Hotness Rubric

Use this rubric after candidate collection and before producing a ranked report.

## Two separate judgements

### Editorial value

How much attention the underlying event deserves, independent of how many articles repeat it.

Evaluate five axes:

1. **Significance:** Does it materially change architecture, capability, compatibility, security, cost, performance, governance, or adoption?
2. **Novelty:** What concrete fact, result, release, method, or constraint is new?
3. **Evidence:** Is the claim backed by an official release, code, advisory, reproducible method, production metrics, or independent confirmation?
4. **Breadth:** How many database, analytics, streaming, platform, or data-engineering teams could reasonably be affected?
5. **Actionability:** Can readers upgrade, mitigate, test, migrate, adopt, or reuse the lesson now?

Do not expose a synthetic numeric score unless the user asks for one. Use the axes to make a comparative editorial judgement.

### Discussion heat

How broadly and recently independent participants are covering the same event.

- Count independent organizations, projects, media outlets, or community authors, not raw URLs.
- Channels with the same catalog `owner_key` count as one participant.
- Give recent coverage more weight than old coverage.
- A useful conceptual decay is a 24-hour half-life over a 48-hour window, but do not present a calculated heat number unless the inputs and computation are explicit.
- One strong official article can be editorially important without being broadly hot.
- A widely repeated event can be hot while its individual articles are weak or repetitive.

## High-value patterns

Treat these normally and often highly:

- stable major releases of databases, engines, table formats, or data platforms;
- security advisories, data-loss risks, compatibility breaks, and required migrations;
- changes to transaction, consistency, concurrency, storage, indexing, query execution, or governance semantics;
- important Kafka KIPs, Flink FLIPs, or equivalent proposals that have shipped or reached a concrete milestone;
- measured production engineering with workload scale, latency, throughput, cost, reliability, or failure data;
- reproducible benchmarks with disclosed datasets, configurations, query definitions, and limitations;
- cross-engine or open-format interoperability involving Iceberg, Paimon, Hudi, Delta, Arrow, Parquet, Fluss, Kafka, or related systems;
- broadly reusable operational, migration, debugging, or capacity-planning methods;
- major foundation, governance, acquisition, licensing, or ecosystem changes with practical consequences.

## Noise controls

Down-rank:

- RC, beta, preview, nightly, and rapid patch churn without a consequential change;
- routine language bindings, minor connectors, ordinary bug fixes, or region availability;
- customer stories without transferable methods or concrete scale/cost/quality results;
- vendor tutorials that only teach the vendor's console;
- event promotion, awards, analyst quadrants, hiring, partnerships without shipped technical consequences, and vague roadmaps;
- benchmarks missing methodology, or claims that compare non-equivalent freshness, correctness, hardware, pricing, or workload boundaries;
- articles that add “AI”, “vector”, “real-time”, or “lakehouse” language without a material data-system change;
- weekly roundups and reposts that contain no original reporting.

## Vendor benchmark handling

Vendor benchmarks may be noteworthy but require explicit qualification:

- say who designed and published the test;
- state the dataset, workload, freshness and correctness boundaries when available;
- separate measured results from the vendor's causal explanation;
- look for an independent response or reproduction;
- do not promote a large ratio into the headline without the boundary next to it.

## Event deduplication

Merge items when they describe the same real-world occurrence, such as:

- official release notes, the vendor blog, GitHub Releases, LinkedIn announcement, and media coverage of one version;
- an ASF announcement and the project's own graduation post;
- multiple articles explaining one security release.

Keep separate:

- a release and a later production case study;
- an announcement and a materially new benchmark;
- a vulnerability disclosure and an unrelated feature release;
- separate follow-up changes that alter availability, price, compatibility, or operational guidance.

## Default report selection

For a weekly report, prefer 8–12 events:

- a small number of urgent security or data-integrity events;
- important stable releases;
- important platform and open-format changes;
- one or two high-quality production engineering reports;
- one or two emerging themes;
- a watchlist for beta releases, vendor claims, or promising but weakly corroborated developments.
