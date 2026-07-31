# Architecture

How `unseea` composes with the GLEN platform, what it adds, and the rule deciding whether something
belongs here or in an application built on it.

Companion to [`DESIGN.md`](DESIGN.md) (what SEEA EA is and how we compile it), [`DATA.md`](DATA.md)
(acquisition) and [`PROVENANCE.md`](PROVENANCE.md) (layer justification).

## What unseea adds

The platform already exists and is deliberately layered. `unseea` adds **one** thing:

> **A Python library implementing the five SEEA accounts behind a narrow API, with a pluggable
> executor — optionally served as an MCP endpoint so any agent can call it.**

Everything else is reuse.

| Component | Role | Owner |
|---|---|---|
| [`data-workflows`](https://boettiger-lab.github.io/data-workflows/) | Legacy → cloud-native Parquet + STAC | upstream |
| [`mcp-data-server`](https://boettiger-lab.github.io/mcp-data-server/) | **The engine.** DuckDB over S3 Parquet, STAC grounding, H3, private routing, mirror failover | upstream |
| [`geo-agent`](https://boettiger-lab.github.io/geo-agent/docs/) | Map + chat + agent loop, config-driven; reproducible chat export | upstream |
| [`geo-agent-benchmark`](https://github.com/boettiger-lab/geo-agent-benchmark) | Question banks, gold provenance ladder, scored runs | upstream |
| **`unseea`** | **The account library** — five accounts, narrow API, executors, bindings, parameter sets, vocabularies | this repo |
| Applications | App config + bindings + parameter sets + private data | separate repos |

**The engine stays upstream.** `mcp-data-server` is explicitly a bridge, not a fork, and is
domain-agnostic by design — its roadmap is engines and data types, not domain semantics. SEEA logic is
therefore an `unseea` artifact, and any genuine *engine* need goes upstream rather than into a server of
our own.

## Why a library rather than example SQL

The tempting alternative is what the platform already does everywhere else: document the tools, put
worked SQL in `system-prompt.md`, and let the agent write queries. That is genuinely good for
exploration, and we keep it.

It is not sufficient for a **statistical standard**, for one narrow reason:

| Property | Provided by | Status |
|---|---|---|
| *What was computed here* is inspectable and re-runnable | `geo-agent` chat export | ✅ already exists |
| *Two sessions compute the same account* | a fixed account definition | ❌ what the library adds |

`geo-agent`'s export already rewrites every `s3://` in a SQL block to
`https://s3-west.nrp-nautilus.io/…`, so exported SQL re-runs in any DuckDB with `httpfs` and no
credentials. That is **session reproducibility**, and it is excellent. What it cannot give is
**specification conformance** — nothing makes two sessions compile the same account, and the SEEALand
fixture can only test a fixed definition.

**A folder of `.sql` files is not a library.** An earlier draft of this document proposed one; there was
no caller, so it would have been example SQL with extra ceremony. The correction matters:

> **SQL is not the interface. It is the returned artifact.**

The API takes structured parameters and hands back the account *plus the exact SQL it ran*. That keeps
the platform's auditability while adding conformance, instead of trading one for the other.

## The API

Small because SEEA fixed the surface — five accounts, fixed table shapes — not because we designed well.

```python
import unseea

eng = unseea.connect(mcp="https://duckdb-mcp.nrp-nautilus.io/mcp")   # or local=True, or fixture=...

eaa  = eng.eaa(country="CR")                    # also basin=, admin=, hex=, geojson=
acct = eng.extent_account(eaa, date=2019)

acct.table        # the SEEA-shaped table
acct.sql          # exact SQL, s3:// rewritten — re-runnable in any DuckDB
acct.checks       # reconciliation results
acct.provenance   # bindings, parameter set, ECT coverage, layer licences
```

Nine calls:

| Call | Returns |
|---|---|
| `connect(...)` | An engine bound to an executor |
| `eaa(...)` | An accounting-area handle |
| `extent_account(eaa, date)` | Area per ET, opening/additions/reductions/closing |
| `extent_change_matrix(eaa, d0, d1)` | The from→to matrix |
| `condition_account(eaa, date, ...)` | All three stages: variables, indicators, index |
| `landscape_metric(eaa, variable, k)` | C1 metrics over a k-ring |
| `services_physical(eaa, date, ...)` | Physical supply-and-use |
| `services_monetary(eaa, date, prices)` | Monetary SUT and GEP |
| `asset_account(eaa, d0, d1, ...)` | NPV per ET plus the area/volume/price decomposition |

Every account call also accepts `bindings=`, `parameters=` and `stratify_by=`.

**The narrowness is a real risk.** A fixed API cannot express "condition by ET *and* by protected-area
status." Two mitigations, both deliberate: `stratify_by` on every account call, and the general `query`
tool stays fully available for anything outside the accounts. That is the two-classes-of-tool split, now
with a mechanism behind it rather than a rule in a prompt.

### Executors

`connect()` is where the runtime choice lives:

| Executor | Runs against | Used for |
|---|---|---|
| **MCP** | The deployed `mcp-data-server` (HPC) | apps, notebooks, agents |
| **Local DuckDB** | NRP directly, or the source.coop mirror | offline analysis, CI against real data |
| **Fixture** | `research/seealand-fixture/` CSVs, **no network** | the conformance tier |

The fixture executor is what makes Phase 1 unblocked by anything — the arithmetic and the NPV
decomposition are forced correct before a single layer is trusted.

### Optional MCP endpoint

Once the library exists, wrapping it as an MCP server is thin, and it is what makes the narrow API
reachable from **every** client — `geo-agent`, Claude Code, `ellmer`, LangChain, notebooks.

A server that *calls* `mcp-data-server` is composition, not a fork; MCP is designed for multiple servers.
The one blocker is that `geo-agent` currently takes a single `mcp_url` — see
[Upstream asks](#upstream-asks). **Build the library first; the server can wait until a web app consumes
it.** All the risk is in the API and the arithmetic, and neither needs a deployment to test.

### Language reach

Python first. R users reach the accounts through the MCP endpoint or by re-running `acct.sql` — not
through a native package. That is a real tradeoff, mitigated by the fact that the **SQL templates are the
shared asset**, so an R wrapper is cheap to add later if demand appears.

## Two arms, compared

We are not asserting the library is better — we are testing it. Both arms get built and scored:

| Arm | What the agent gets |
|---|---|
| **A · Narrow API** | The nine account tools; general `query` for exploration only |
| **B · Prompt + examples** | Worked SQL in `system-prompt.md`; the agent writes account SQL itself |

Arm B has more flexibility and more room for error, and the gap should narrow as models improve — which
is exactly why it needs measuring rather than assuming.

Scored in [`geo-agent-benchmark`](https://github.com/boettiger-lab/geo-agent-benchmark), which already
provides question banks, a gold-provenance ladder and scored runs. **SEEALand gold is L3 on that ladder
by construction** — it matches a published professional source (the standard itself) with tolerance,
which is the strongest rung available.

What to measure: accuracy against fixture and golden values, **run-to-run variance on identical
questions** (the property Arm B structurally cannot guarantee), latency, token cost, and how each arm
degrades on weaker models.

## Private data

Established pattern, adopted rather than reinvented.

**Preferred — a credentialed replica** (`boettiger-lab/wyoming` prior art). A dedicated
`mcp-data-server` replica routes `s3://private-*` through a **scoped DuckDB secret** from its own
environment, behind a sidecar injecting the bearer token and rewriting `catalog_url` to the
cluster-internal host. Credentials appear in **no JSON-RPC body at all**, not even the internal hop — and
tools without `s3_*` parameters (e.g. `register_hex_tiles`) work on private data, which per-request
injection can never provide.

**Simpler — per-request credentials.** `query` accepts `s3_key`, `s3_secret`, `s3_endpoint`, `s3_scope`
per call; fresh `duckdb.connect(":memory:")` per request, `stateless_http=True`, `CREATE SECRET` never
logged, and `geo-agent` redacts all of these keys from live chat and export. Fine for scripts.

⚠️ **Always pass `s3_scope` when mixing buckets.** A bare `s3_endpoint` applies to every `s3://` path and
disables the server default, silently breaking public catalog reads — a further argument for the replica
pattern, where scoping lives in server config rather than every call site.

This is what makes **a public application repo with private data access** coherent: the repo holds
bindings, parameter sets and reference levels — the methods — while data is reached by credential at
runtime. Better for transparency, since reference levels are exactly what reviewers should see.

## Licence: the obligation we propagate

Not "are we commercial" — we are not. The question is **what obligation we pass to users.**

CC BY-NC data propagates its restriction into derived research, data and tools. A published tool built on
NC data passes it on: a downstream user could not use the platform commercially without separately
licensing the data. So:

- **Every binding declares its licence**, carried into `acct.provenance` and any export.
- Accounts built on an NC layer are **labelled NC-encumbered**, so users know what they hold.
- Applications may set a **licence policy** and have out-of-policy bindings rejected rather than silently
  included.

`irrecoverable-carbon` is CC BY-NC 4.0, so any global-climate-regulation account built on it is
encumbered — usable and honest, a problem only if unstated. WDPA has separate open questions
([#14](https://github.com/SchmidtDSE/unseea/issues/14)).

## Test tiers

SEEA hands us the suite: **every account reconciles by construction**, so invariants are derivable rather
than invented, and the fixture ships `Check` rows at ~1e-10.

| Tier | Executor | Catches |
|---|---|---|
| **Fixture** | fixture, no network | Conformance — GEP $83,125, forest ΔNPV −$116,366 |
| **Golden** | local or MCP | Catalog and engine drift — Costa Rica extent at −0.20% |
| **Property** | any | Structural violations on real data |

| Account | Invariant |
|---|---|
| Extent | opening + additions − reductions = closing; total = EAA area |
| Change matrix | row sums = opening extent; column sums = closing extent |
| Condition | Σ ECT-class changes = net change; every index ∈ [0,1] |
| Supply and use | total supply = total use, per service |
| Asset | opening + all entries = closing; area + volume + price = ΔNPV |

## Where the agent sits

> **The agent selects and parameterizes account compilations. It does not author account arithmetic.**

Exploratory SQL stays fully available and reproducible via the chat export. It is simply a different
class of work, and the distinction must be visible in the output so nobody mistakes an exploratory query
for a SEEA account.

The agent still does the interpretive work: delimiting the EAA from natural language, choosing which
account or scenario answers the question, stating assumptions before results (`DESIGN.md` §5.2, §5.3),
naming ECT coverage (§2.4), narrating caveats, and exploring around the edges.

## Upstream asks

Small, and each is generically useful beyond us:

| Ask | Repo | Why |
|---|---|---|
| **Multiple MCP endpoints** per app (`mcp_url` is singular today) | `geo-agent` [#338](https://github.com/boettiger-lab/geo-agent/issues/338) | Lets an app combine the generic engine with a domain server. Needed for Arm A in the browser |
| **XLSX export** | `geo-agent` | The HTML chat export is excellent but statistical-office users need spreadsheets |
| **Reactive parameter controls** | `geo-agent` | Discount rate, asset life, carbon price, reference basis want persistent controls, not chat turns — shared with landscape-frontiers' weight slider (#147) |

## Applications

An application is a `geo-agent` app (`layers-input.json`, `system-prompt.md`, `k8s/`) plus its own
bindings and parameter sets, pinning an `unseea` version.

**Cocoa builds on [`SchmidtDSE/cacao-demo`](https://github.com/SchmidtDSE/cacao-demo)**, extending
and replacing as needed. That app was an early framing of these ideas on the GLEN/geo-agent architecture
— useful base layers, but without the machinery to walk a user through a SEEA analysis or produce the
reports. It already has the deployment, the feedback loop and a Peru layer selection; a new repo would
abandon working infrastructure to avoid a rename.

Deployment shape for a public app over private data: `boettiger-lab/wyoming`.

### The composition invariant

> **If an application requires a change to the account library, the abstraction is wrong.** Applications
> add bindings, parameter sets, vocabularies and data.

> **If unseea needs a new engine capability, it goes into `mcp-data-server`.**

### The filing rule

Ask: **would this still be true for a different commodity, partner or region?**

| Goes in `unseea` | Goes in the application repo |
|---|---|
| Facts about SEEA and what it permits | The specific comparison being made |
| Constraints binding every application | Partner identity, agreements, private data |
| Application *patterns* (e.g. working lands, `DESIGN.md` §5.4) | Reference levels for one production system |
| Gap *classes* (e.g. practice-response coefficients) | The specific coefficients and yields |
| Anything needed to replicate a published account | Anything under NDA |

A finding that resists filing is evidence the seam is wrong. Record that rather than forcing it.

## Deliberately not built

- **No fork of `mcp-data-server`.** Engine needs go upstream.
- **No MCP server until the library exists** and a web app needs it.
- **No R package** until demand appears; the SQL templates make one cheap later.
- **No binding DSL or plugin API** until two real consumers exist — the reference app and the first
  application. The application's arrival is the *test* of whether the seam was right; gold-plating it
  beforehand is how modular designs acquire their own hot glue.
