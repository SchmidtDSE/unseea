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

**Scoping.** No application code yet. Start with [`DESIGN.md`](DESIGN.md), then the roadmap in
[**issue #20**](https://github.com/SchmidtDSE/unseea/issues/20).

Phases 1–2 need no new data ingest — deliberately, so the account-arithmetic correctness work runs in
parallel with data acquisition rather than behind it.

## Contents

| Path | What |
|---|---|
| [`DESIGN.md`](DESIGN.md) | The design document: what SEEA EA is, how ARIES for SEEA compares, the hard problems, the interaction model, and a phased plan |
| [`DATA.md`](DATA.md) | Best-in-class data acquisition plan: UNSD Tier framework, per-account source selection, licence analysis, and how it lines up against the `data-workflows` tracker |
| [`research/seea-ea-reference.md`](research/seea-ea-reference.md) | Distilled controlled vocabularies and table structures from the standard — the source for `system-prompt.md` and the app's lookup tables |
| [`research/`](research/) | The SEEA EA standard (393 pp) and the UNSD Guidelines on Biophysical Modelling (221 pp), as published plus text extractions |

## Why this stack

SEEA builds accounts up from **basic spatial units** and states that its area-weighted aggregation is
invariant to the resolution the data are collated at (footnote 172). An H3 tessellation with
area-weighted rollup is therefore not an approximation of the SEEA spatial model — it is that model,
implemented. Every account reduces to a `GROUP BY` over hex cells joined to an accounting area, which is
what makes live scenario recomputation feasible at all.

## Nearest prior art in the lab

[`landscape-frontiers`](https://github.com/boettiger-lab/landscape-frontiers) — same pattern: fork
`geo-agent-template`, configure three files (`layers-input.json`, `system-prompt.md`, `k8s/`), keep the
computation in SQL against the duckdb-geo MCP, and let fidelity scale with the catalog ingest.
