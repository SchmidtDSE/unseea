# unseea

A **UN SEEA-EA decision planning tool** built on the [`geo-agent`](https://github.com/boettiger-lab/geo-agent)
runtime and the GLEN h3 data catalog.

SEEA Ecosystem Accounting is the UN statistical standard (adopted March 2021) for organising
biophysical and economic information about ecosystems into five reconciling accounts. The standard ships
a worked toy example, **SEEALand** — 250 hectares, six ecosystem types, one land-cover conversion,
carried through all five accounts.

**This app is SEEALand for any polygon on Earth, with real data, computed live — plus the scenario
branch the standard never runs.** Draw an area, get its five SEEA accounts; then propose a land-use
change and watch the accounts recompute into the standard's own vocabulary: managed expansion, managed
reduction, degradation, enhancement, revaluation.

## Status

**Phase 1 — the account library.** The five accounts are implemented behind a nine-call API and
reproduce SEEALand end to end against the standard's own published figures, with no network. No
application code yet. Start with [`DESIGN.md`](DESIGN.md), then the roadmap in
[**issue #20**](https://github.com/SchmidtDSE/unseea/issues/20).

```python
import unseea

eng  = unseea.connect(fixture="research/seealand-fixture/")   # or local=True, or mcp=url
eaa  = eng.eaa()
acct = eng.asset_account(eaa, 2020).check()

acct.tables["asset"]   # the SEEA-shaped table: entries down, ecosystem types across
acct.sql               # the exact SQL that produced it, re-runnable
acct.checks            # opening + entries = closing; area + volume + price = ΔNPV
acct.provenance        # executor, parameters, ECT coverage, sources, licences
```

```console
$ pip install -e ".[test]" && pytest -q
157 passed
```

| Call | Returns |
|---|---|
| `connect(fixture=… / local=True / mcp=url)` | An engine bound to an executor |
| `eaa(...)` | An accounting-area handle |
| `extent_account(eaa, date)` | Area per ET: opening, additions, reductions, closing |
| `extent_change_matrix(eaa, d0, d1)` | The from→to matrix, with margins |
| `condition_account(eaa, date)` | All three stages: variables, indicators, index |
| `landscape_metric(eaa, variable, k)` | C1 metrics over a k-ring — needs an h3 executor ([#7](https://github.com/SchmidtDSE/unseea/issues/7)) |
| `services_physical(eaa, date)` | Physical supply and use |
| `services_monetary(eaa, date, prices)` | Monetary supply and use, and GEP |
| `asset_account(eaa, d0, d1)` | NPV per ET plus the area/volume/price decomposition |

The fixture executor is the **conformance tier**: it runs the SEEALand CSVs through DuckDB with no
network, and CI fails loudly if GEP drifts from $83,125 or forest ΔNPV from −$116,366. The `local`
and `mcp` executors are declared but not yet implemented — each raises an error naming the issue
that blocks it.

📖 **[Documentation site →](https://schmidtdse.github.io/unseea/)** — begins with a walkthrough of
[**SEEALand**](https://schmidtdse.github.io/unseea/seealand.html), the standard's worked toy example,
traced through all five accounts.

Phases 1–2 need no new data ingest — deliberately, so the account-arithmetic correctness work runs in
parallel with data acquisition rather than behind it.

## Contents

| Path | What |
|---|---|
| [`src/unseea/`](src/unseea/) | **The account library:** five accounts as SQL, three executors, parameter sets and vocabularies |
| [`tests/`](tests/) | The conformance tier: SEEALand reproduced cell by cell, plus the library contract |
| [`DESIGN.md`](DESIGN.md) | The design document: what SEEA EA is, how ARIES for SEEA compares, the hard problems, the interaction model, and a phased plan |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | **How the system is layered:** the account-compiler contract, the binding/parameter/vocabulary seam, licence and private-data policy, test tiers, and the rule deciding what belongs here versus in an application built on it |
| [`DATA.md`](DATA.md) | Best-in-class data acquisition plan: UNSD Tier framework, per-account source selection, licence analysis, and how it lines up against the `data-workflows` tracker |
| [`PROVENANCE.md`](PROVENANCE.md) | **The planned layer list, with justification:** for each layer, is it named in SEEA/UNSD guidance, used by ARIES, used in a published national account, or our own judgement — plus the roadmap issue tracking it |
| [`research/seea-ea-reference.md`](research/seea-ea-reference.md) | Distilled controlled vocabularies and table structures from the standard — the source for `system-prompt.md` and the app's lookup tables |
| [`research/`](research/) | Source documents: the SEEA EA standard (official 2024 ed.), UNSD Guidelines on Biophysical Modelling, UNSD Monetary Valuation technical report, and the official SEEA supplements — including the **SEEALand worked example as CSV test fixtures** |

## Why this stack

SEEA builds accounts up from **basic spatial units** and states that its area-weighted aggregation is
invariant to the resolution the data are collated at (SEEA EA (2024 official ed.), Annex I, Table AI.5, footnote c). An H3 tessellation with
area-weighted rollup is therefore not an approximation of the SEEA spatial model — it is that model,
implemented. Every account reduces to a `GROUP BY` over hex cells joined to an accounting area, which is
what makes live scenario recomputation feasible at all.

## Nearest prior art in the lab

[`landscape-frontiers`](https://github.com/boettiger-lab/landscape-frontiers) — same pattern: fork
`geo-agent-template`, configure three files (`layers-input.json`, `system-prompt.md`, `k8s/`), keep the
computation in SQL against the duckdb-geo MCP, and let fidelity scale with the catalog ingest.
