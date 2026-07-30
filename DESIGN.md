# unseea — a UN SEEA-EA decision planning tool on the geo-agent runtime

**Status:** scoping design document. No code yet.
**Sources:** SEEA EA (2021) White Cover, 393 pp — full text extracted and quoted below; ARIES for SEEA
Explorer user guide; the GLEN STAC catalog (223 collections) as of 2026-07-30.

---

## 1. The one-sentence idea

SEEA EA ships a worked example called **SEEALand** — a 250-hectare toy landscape with six ecosystem
types, carried through all five accounts for one accounting period, ending in a monetary asset account
and a Gross Ecosystem Product of $83,125.

**This app is SEEALand for any polygon on Earth, with real data, computed live, plus the scenario
branch the standard never runs.** A user draws a watershed, names a country, or clicks a hex; the agent
compiles the five SEEA accounts over that ecosystem accounting area; then the user proposes a change —
convert this, protect that, restore the other — and the same five accounts recompute so the deltas land
in the standard's own vocabulary: managed expansion, managed reduction, degradation, enhancement,
revaluation.

That last move is the product. Everything else is table stakes that ARIES already partly covers.

---

## 2. What UN SEEA-EA actually is

The **System of Environmental-Economic Accounting — Ecosystem Accounting** (SEEA EA) was adopted by
the UN Statistical Commission in March 2021. It is a *statistical standard*, not a model or an
assessment method: it specifies how to organise biophysical and economic information about ecosystems
into double-entry-style accounts that reconcile with the System of National Accounts (SNA).

Two consequences shape the whole design:

1. **Accounts, not maps.** The deliverable is a set of tables with opening balances, additions,
   reductions, and closing balances that must add up. A map is an input and a diagnostic, never the
   output. Our app must therefore be a *table generator* first and a map second — the inverse of most
   geo-agent apps.
2. **Exchange values, not welfare values.** Monetary entries must be SNA-consistent exchange values.
   Willingness-to-pay, consumer surplus, and most stated-preference numbers are explicitly *out* of the
   core accounts (they belong in the Ch. 12 "complementary approaches" bridge table). This rules out a
   large fraction of the ecosystem-services valuation literature.

### 2.1 The five accounts

Verbatim from Table 2.1:

| # | Account | Terms |
|---|---|---|
| 1 | Ecosystem extent account | physical |
| 2 | Ecosystem condition account | physical |
| 3 | Ecosystem services flow account | physical |
| 4 | Ecosystem services flow account | monetary |
| 5 | Monetary ecosystem asset account | monetary |

They chain: extent and condition describe the asset; condition drives the *capacity* to supply
services; physical service flows × exchange prices give monetary flows; the discounted stream of
expected future monetary flows gives the asset value. Degradation is then *defined* as the fall in
asset value attributable to a decline in condition — which is why you cannot shortcut to a headline
"value of nature" number without first doing the extent and condition work.

### 2.2 The four spatial units — and why H3 is an unusually good fit

| SEEA unit | Definition | Our mapping |
|---|---|---|
| **BSU** — basic spatial unit | The finest tessellation; a grid the accounts are built up from | **An H3 cell.** Global layers follow the catalog's res-8 convention (≈ 0.74 km²); CONUS NLCD reaches res 10 (≈ 0.015 km²) |
| **ET** — ecosystem type | The class an area is assigned to; reference classification is IUCN GET | IUCN GET Level 3 (EFG), resolved per §5.1 |
| **EA** — ecosystem asset | A contiguous, non-overlapping area of one ET | The set of BSUs of one ET within the EAA |
| **EAA** — ecosystem accounting area | The reporting boundary: country, province, river basin, protected area | Overture divisions, HydroBASINS, USGS WBD, WDPA, or a drawn polygon |

The standard is emphatic that accounts are aggregated up from BSUs, and — critically for us — that the
area-weighted approach makes results **scale-invariant**:

> "an area-weighted approach has been used meaning that the overall index is invariant to whether the
> data are collated at finer resolutions (e.g. pixels) or at larger resolutions (e.g. for the ecosystem
> asset)." — SEEA EA, footnote 172

That footnote is a licence for exactly what GLEN does. An H3 tessellation with area-weighted
aggregation and parent-index rollup is not an approximation of the SEEA spatial model; it *is* the SEEA
spatial model, implemented. Every account below reduces to a `GROUP BY` over hex cells joined to an EAA.

### 2.3 Ecosystem extent (Ch. 4)

The account is `accounting entries × ecosystem types`, in area units:

```
Opening extent
Additions to extent      → Managed expansion   / Unmanaged expansion
Reductions in extent     → Managed reduction   / Unmanaged reduction
Net change in extent
Closing extent
```

Plus an **ET change matrix** (Table 4.2): opening types as rows, closing types as columns, unchanged
area on the diagonal. This is a from→to transition matrix — trivially a two-year `GROUP BY` on hex.

The reference classification is the **IUCN Global Ecosystem Typology**, 25 biomes across 5 realms
(Table 3.2): terrestrial T1–T7, freshwater F1–F3, marine M1–M4, subterranean S1–S2, and nine
transitional biomes (TF1 palustrine wetlands, MT1 shoreline systems, MFT1 brackish tidal, etc.).
Accounts are compiled at **Level 3, Ecosystem Functional Group** (~110 EFGs).

Note the standard's own hedge: "Compilation will require the use of nationally selected ecosystem
types." Countries are expected to deviate; conformance means being crosswalkable to GET, not identical.

### 2.4 Ecosystem condition (Ch. 5)

Three nested accounts, and the app must produce all three because each answers a different question:

- **Variable account** — raw measured values per condition variable, opening and closing.
- **Indicator account** — each variable rescaled to [0,1] against a **lower and upper reference level**.
- **Index account** — indicators weighted into sub-indices per ECT class, then an overall index.

Variables are organised by the **SEEA Ecosystem Condition Typology (ECT)**, six classes in three groups:

| Class | Content |
|---|---|
| A1 Physical state | soil structure, water availability, % bare ground, % burnt area |
| A2 Chemical state | soil organic carbon, nutrient levels, water quality, air pollutants |
| B1 Compositional | species richness/abundance, share of non-native species |
| B2 Structural | tree cover density, biomass, canopy layers, deadwood volume |
| B3 Functional | primary productivity, community age, disturbance frequency |
| C1 Landscape | landscape diversity, connectivity, fragmentation, edge:interior ratio |

**Reference levels are the crux.** An indicator is meaningless without them, and SEEA offers five
possible reference conditions (Table 5.9) — undisturbed/minimally-disturbed, historical,
least-disturbed, contemporary, best-attainable — estimated by reference sites, modelling, ambient
statistical distributions, paleo data, contemporary data, prescribed levels, or expert opinion.
Natural and anthropogenic ETs get *different* reference conditions, and the standard forbids averaging
condition across them:

> "An average measure of ecosystem condition across all ET has not been derived as this would imply
> aggregation across different reference conditions and this is not recommended."

Design consequence: reference levels must be an explicit, inspectable, user-overridable object in this
app, not a hidden constant. This is where an agent earns its place — it can *explain* which reference
condition was assumed and let the user change it.

### 2.5 Ecosystem services (Ch. 6–7, 9)

The **reference list of selected ecosystem services** (Table 6.3) is the controlled vocabulary. Full
list, with what we could compute (§4):

*Provisioning* — crop; grazed biomass; livestock; aquaculture; wood; wild fish and other natural
aquatic biomass; wild animals/plants; genetic material; water supply.

*Regulating and maintenance* — global climate regulation; rainfall pattern regulation (sub-continental);
local climate regulation; air filtration; soil quality regulation; soil erosion control; landslide
mitigation; solid waste remediation; water purification (nutrients / other pollutants); water flow
regulation (baseline flow / peak flow); flood control (coastal protection / river flood mitigation);
storm mitigation; noise attenuation; pollination; biological control (pest / disease); nursery
population and habitat maintenance.

*Cultural* — recreation-related; visual amenity; education, scientific and research; spiritual, artistic
and symbolic.

Recorded as **supply and use tables**: rows are services, columns are supplying ecosystem types
(supply) or using economic units — industries, households, government, accumulation, exports (use).
Two traps we must not fall into:

- **Final vs intermediate.** Only *final* services count toward the headline aggregate. Several entries
  (genetic material, soil quality regulation, nursery/habitat maintenance, pollination) are usually
  *intermediate* — inputs to other services. Double-counting them is the classic ecosystem-services
  error, and the accounting structure exists specifically to prevent it.
- **Ecosystem contribution, not total output.** "Crop provisioning services are the ecosystem
  contributions to the growth of cultivated plants" — not the tonnage, and not the farm-gate revenue.
  The ecosystem's share must be separated from labour, capital, and inputs. This is what resource-rent
  and residual-value methods are for, and it is the single most common way naive implementations
  overstate the accounts by an order of magnitude.

**Gross Ecosystem Product (GEP)** = sum of final ecosystem services in monetary terms, less net imports
of intermediate services. This is the natural headline number for a decision tool.

### 2.6 Monetary accounts (Ch. 8–11)

Valuation is at **exchange values** (Ch. 8). Permitted techniques (Ch. 9) run from directly observed
prices, through resource rent / residual value, replacement cost, averting behaviour and travel cost,
to production-function approaches. SEEALand's assumed prices give the flavour: wood $60/m³, crop
$75/tonne, wild fish $350/tonne, global climate regulation $25/tCO₂, water purification $100/tonne N
removed, recreation $5/visit.

The **monetary ecosystem asset account** (Table 10.1) is NPV of expected future service flows, with
SEEALand's assumptions: 100-year asset life, 2% real discount rate, income at period end. Its power —
and its difficulty — is the *decomposition* of the change in asset value into:

```
Opening value
+ additions (managed / unmanaged expansion)
− reductions
− degradation          ← condition decline reduces expected future flows
+ enhancement          ← condition improvement
± ecosystem conversions
± revaluation          ← changed expected prices
= Closing value
```

Reproducing that decomposition correctly is the hardest computational piece in the whole standard, and
it is the piece that makes the tool a *decision* tool: "your proposed conversion causes $X of
degradation and $Y of revaluation" is a sentence a finance ministry can act on.

---

## 3. ARIES for SEEA — what exists, and the gap we fill

[ARIES for SEEA Explorer](https://seea.un.org/en/data/aries-for-seea) is the incumbent and the honest
benchmark. Built on the k.LAB Integrated Modelling platform, it uses semantic-web machine reasoning to
auto-select models based on the user's location, resolution and requested account — genuinely
impressive, and a real standard-setter for provenance.

**What it does:** user picks a context (map bounds, UN M49 admin region, or FAO hydrological basin),
sets spatial resolution and one or many years; ARIES returns extent accounts (IUCN GET or land cover),
condition accounts (forest only, grassland forthcoming — as variable/indicator/index accounts, matching
§2.4), four physical ecosystem services, and three monetary ones. Outputs are interactive tables, Excel
downloads, GeoTIFFs, and an auto-generated report documenting data, models, coefficients and caveats.
English/French/Spanish.

**Its stated limits:**

- Terrestrial only.
- Condition accounts cover **forests only**.
- **Four** ecosystem services of the ~27 in the reference list — crop provisioning, crop pollination,
  global climate regulation, soil erosion control; nature-based tourism in development. Water supply
  and flood regulation are explicitly future work.
- Aggregation is **whole-context only** — no breakdown by admin subregion, protected area, or
  watershed yet.
- A candid modelling caveat: crop spatialisation "assumes crop extent to be constant… with only crop
  yield changing over time — an assumption we know to be false."
- Requires registration on the Integrated Modelling Hub; model runs take real time.

**The gap.** ARIES is a *compiler* of accounts for the present state. It has no notion of a
counterfactual. Nothing in it answers "what would this account look like if we converted 2 000 ha of
forest to cropland, or restored this wetland, or extended this protected area?" — which is precisely the
question a planning ministry brings. Add to that: no arbitrary AOI aggregation, no sub-EAA breakdown,
forest-only condition, and 4 of 27 services.

**So our four differentiators, in priority order:**

1. **Scenario / what-if planning.** Propose a land-use change; get the account deltas in SEEA's own
   vocabulary. Nothing else does this. §6 details the mechanism.
2. **Any-AOI interactive speed.** H3 + DuckDB over cloud-optimised parquet turns each account into one
   `GROUP BY`. Sub-second, any polygon, any nesting — and free disaggregation by subregion/PA/basin,
   which is on ARIES's roadmap and is a natural consequence of our data model rather than a feature.
3. **Agent-driven narration and audit trail.** The agent states which account, which variable, which
   reference level, which valuation method, and what it could not compute — then emits the tables. This
   is the honest way to lower the expertise barrier, and it must include a machine-readable methods
   record to match ARIES's provenance standard.
4. **Replication and validation.** Reproduce SEEALand exactly, then published national accounts, and
   quantify where global-data shortcuts diverge from official compilations. Credibility is the product
   here; without this we are a demo.

We should be explicit and non-competitive in framing: ARIES is the reference implementation for
*compilation*; we are a fast, interactive *exploration and scenario* layer that should agree with it
wherever both can compute the same account. Divergence is a finding, not a win.

---

## 4. Data: what GLEN has, and what it doesn't

Assessed against the 223-collection catalog. This is the section that determines what v1 can honestly claim.

### 4.1 Strong today

| SEEA need | Layer | Note |
|---|---|---|
| EAA delineation | `overture-divisions-*` (countries/regions/counties), `hydrobasins-v1c`, `usgs-wbd` (HUC2–12), `protected-planet`/`wdpa`, `wdoecm-may-2026` | Covers admin, basin and PA reporting boundaries — already broader than ARIES's three context types |
| Extent, wall-to-wall, exact areas | `cgls-lc100-2019` **hex-fractions** (res 9, 23 LCCS classes) | `frac` × cell area = exact per-class area. One row per (cell, class) — the right primitive. **2019 only** |
| Extent + change, CONUS | `nlcd-2024` hex-fractions (res 10, 16 classes), annual series | True opening/closing extent and ET change matrix, today, for CONUS |
| Condition B1 compositional | `globio-msa-2015-overall` (+ plants / warm-blooded vertebrate variants; res 8) | **MSA is already a SEEA indicator**: intactness in [0,1] against an undisturbed reference. The reference level is built in. Also has 2050 SSP1/SSP3/SSP5 scenarios — a ready-made condition trajectory |
| Condition B1 | `iucn-richness-2025`, `iucn-ranges-2025`, `mobi-species-richness-all` | Species richness variables |
| Condition, pressure-side | `global-human-modification`, `nci-frontiers` FLII (forest landscape integrity) | Ch. 5.5.3 permits pressure data with care |
| Condition C1 landscape | *computed from the hex land cover itself* | See §4.4 — this is a genuine structural advantage |
| Global climate regulation (stock) | `irrecoverable-carbon` (v2 2024, res 9, Mg C) | Carbon *retention*. Not sequestration — see gaps |
| Crop / grazed biomass / wood provisioning | `nci-frontiers` (crop, palm, grazing, forestry $/ha; res 5/8) | CC0 from Polasky et al. 2026. Revenue densities, so a residual-value step is still needed to isolate the ecosystem contribution |
| Wild fish provisioning | `gfw-fishing-effort` (2012–2024) | Effort, not catch — a proxy |
| Nursery / habitat maintenance | `kba`, `imma`, `ebsa`, `iucn-ranges-2025` | Intermediate service |
| Recreation (US) | `parkserve-2025-*`, `federal-trails-2026`, `protected-planet` | Visits proxy; US-strong, global-weak |
| Beneficiaries / use table | `ghs-pop-2020`, `acs-2020-2024-blockgroup` | Needed to allocate use to economic units |
| Marine / transitional ETs | `meow-ecoregions`, `seafloor-geomorphology`, `gebco-2025`, `wetlands-global-unified` (Ramsar/GLWD/NWI) | Real coverage of GET marine and transitional realms — ARIES is terrestrial-only, so this is open ground |

### 4.2 The three blocking gaps

1. **No global land-cover time series.** `cgls-lc100-2019` is a single year. Without two time points
   there is no opening extent, no closing extent, no change matrix, no conversion entries — and
   therefore no degradation attribution and no monetary asset account. **This blocks four of the five
   accounts outside CONUS.** Highest-priority ingest.

2. **No ecosystem-type classification.** SEEA's reference classification (IUCN GET) and the wall-to-wall
   partition it needs (World Terrestrial Ecosystems) are both absent from the catalog — though both are
   already queued together as data-workflows **#438**, with GET currently a stretch goal.

3. **No carbon flux.** We have carbon *stock* (`irrecoverable-carbon`), but SEEA global climate
   regulation covers both "removal (sequestration) of carbon" and "retention (storage) of carbon". The
   sequestration flow — the part that behaves like an annual service — is missing. Queued biomass work
   (**#445**) covers stock, not flux.

4. **No economic spine.** Nothing in the catalog supports the *use* side of the service accounts or the
   resource-rent step the monetary accounts require. See [`DATA.md`](DATA.md) §6.

### 4.3 Ingest strategy

**Full best-in-class acquisition plan, licence analysis and sequencing: [`DATA.md`](DATA.md).**

The short version, after auditing the `data-workflows` tracker: **most of what unseea needs is already
queued.** Epic **#449** (TNFD/SBTN global gaps) plus **#453** (NLCD Annual, scope-locked) covers roughly
two-thirds of the requirement, and its LEAP/SBTN framing maps almost cell-for-cell onto SEEA's accounts —
*Locate* ≈ extent, *Assess* ≈ condition, *Evaluate* ≈ services.

The genuine net-new asks are:

| Ask | Why it matters | Status |
|---|---|---|
| **GLC_FCS30D** (30 m, 1985–2022, annual from 2000, 35 classes) as annual `hex-fractions` | The only route to global extent *change*. #439 is two epochs, #453 is CONUS-only — nothing queued gives this. Blocks four of five accounts outside CONUS | ❗ **file** |
| **NPP / dry-matter productivity** | Condition ECT class **B3 functional is entirely empty**; one ingest fills it | ❗ file |
| **GFW/Harris forest carbon flux** | #445 gives carbon *stock*; the annual *removal* flux half of global climate regulation is missing | ❗ file |
| **SPAM 2020 + FAOSTAT** | Turns crop provisioning from a revenue proxy into a real service (Vallecillo contribution step) | ❗ file |
| **EXIOBASE 3 · ESVD · ENCORE** | The economic spine — resource rent, use tables, service imports/exports, value transfer. Wholly absent from the tracker, and a different *kind* of artefact (national/sectoral lookup tables, not hexed rasters) | ❗ decide where these live |

Plus two comments on existing issues rather than new work: **#438** and **#439** should ship a
**`hex-fractions` asset alongside `mode`** — at the epic's global convention of native res 8 (~0.74 km²),
mode discards the within-cell class mix and materially distorts per-class area, so the extent account's
balance check would fail for reasons unrelated to the data. #453 is already scope-locked to
"hex-fractions-first", so this is extending an accepted decision, not proposing a new one. #438 should
also promote IUCN GET from stretch goal to in-scope.

Everything here lights up specific account rows without app changes — the same "fidelity scales with the
ingest" property that landscape-frontiers relies on. DESIGN.md Phases 1–2 need **no new global ingest at
all**.

### 4.4 The landscape-metrics advantage

ECT class **C1 (landscape/seascape)** — connectivity, fragmentation, landscape diversity, forest area
density, edge:interior ratio — is normally the most laborious part of a condition account, requiring
dedicated raster tooling (FRAGSTATS and friends).

On an H3 grid it is nearly free. `h3_grid_disk` gives a cell's neighbourhood directly, so forest area
density is the mean forest fraction over a k-ring; fragmentation is the share of neighbours in a
different class; landscape diversity is Shannon entropy over neighbourhood class fractions. All are
single SQL window/aggregate expressions over data we already hold, at any k, for any AOI.

SEEA's own worked example leans on exactly these variables — SEEALand's forest condition decline is
driven mostly by "a large decrease in forest area density, a proxy for forest connectivity". So the
metric family that H3 makes cheap is the one the standard reaches for first. This is worth building
carefully and worth advertising.

---

## 5. The hard problems, and proposed resolutions

### 5.1 IUCN GET maps are indicative and overlapping — they cannot be summed

This is the central technical risk of the chosen scope, and it needs stating plainly.

The GET Level 3 maps are **indicative distribution maps**, built "on a coarse-scale template (e.g.
ecoregions)", flagging **major (1)** and **minor (2)** occurrence, where minor means an EFG is
"scattered in patches within matrices of other ecosystem functional groups". They **overlap**: a given
location can be flagged for several EFGs. Level-3 maps are explicitly *not* intended to represent
fine-scale pattern.

Therefore: rasterising GET and summing areas per EFG would double-count, would report EFG areas far
larger than reality, and would fail the extent account's own internal check that ET areas sum to the
EAA. An extent account built that way is not conservative or approximate — it is arithmetically wrong.

**Proposed resolution — three layers with three distinct jobs.** (Revised after reviewing the
`data-workflows` tracker; see [`DATA.md`](DATA.md) §3.1 for the full reasoning.)

- **World Terrestrial Ecosystems 2020** (USGS/Esri/TNC, 250 m, 431 classes — tracked as data-workflows
  **#438**) is **the ET partition**: wall-to-wall, mutually exclusive, so ET areas sum to the EAA.
  SEEA EA §3.67 names it explicitly as a classification to develop correspondences for, and its
  landcover × climate × landform decomposition is a far better crosswalk basis than a land-cover legend
  alone.
- **GET** supplies the **reference-classification label**, attached to WTE classes by crosswalk. Its
  major/minor occurrence becomes a *validation* signal on that crosswalk rather than a load-bearing
  input — which is the right role for an indicative map.
- **A land-cover time series** is **the change detector**, driving the additions and reductions entries.
  WTE is a single 2020 epoch and cannot supply change on its own.

Ties and gaps break by ecoregion (`wwf-ecoregions-2017`, `meow-ecoregions`) and realm priority.
Anthropogenic classes route to the T7 intensive-land-use and M4 / MT3 / F3 anthropogenic biomes, which is
what those biomes are for.

Then publish, always, alongside the extent account:

- the share of EAA area resolved to a **major**-occurrence EFG (high confidence),
- the share resolved only via **minor** occurrence or crosswalk fallback (low confidence),
- the share **unresolvable / ambiguous**.

That third number is the honesty check, and it must appear in the agent's narration, not just a
footnote. Where it is large, the app should report extent at GET **biome** level (25 classes) rather
than EFG level — coarser, but defensible. The standard's "nationally selected ecosystem types" clause
is what makes this conformant.

Building the crosswalk is real work — a curated lookup table, reviewed by someone with ecological
standing, versioned in-repo. It should not be improvised by the agent at query time. There is prior art
to follow: data-workflows **#427** imports the IUCN habitat ↔ land-cover crosswalk (Lumbierres 2021) as
an AOH/STAR prerequisite — same shape of artefact, same review burden.

### 5.2 Monetary valuation is where credibility is won or lost

The chosen scope includes all five accounts, so we own the valuation problem. Three guardrails:

- **Ecosystem contribution ≠ output value.** `nci-frontiers` gives crop and grazing *revenue* per
  hectare. Booking that as crop provisioning service value would overstate the account by whatever
  share of revenue is attributable to labour, capital and purchased inputs. A residual-value /
  resource-rent step is mandatory, and its assumptions must be surfaced.
- **The carbon price is contested.** SEEALand uses $25/tCO₂ and the standard permits "carbon trading
  schemes or data on the social cost of carbon (under appropriate assumptions)" — but the SCC is a
  welfare-based damage cost, and using it as an exchange value sits uneasily with Ch. 8. Make the
  carbon price an explicit, user-settable parameter with a documented default, and show the account's
  sensitivity to it rather than burying a single number.
- **Discount rate and asset life dominate the asset account.** At 100-year life, moving 2% → 4% roughly
  halves NPV. These must be visible controls with SEEALand's defaults, and the app should quote the
  asset account as a range, not a point.

Recommendation: gate the monetary accounts behind an explicit, always-visible assumptions panel, and
have the agent refuse to state an asset value without also stating the discount rate, asset life and
carbon price it used. A wrong-looking big number will discredit the whole tool faster than a missing one.

### 5.3 Condition reference levels cannot be global constants

Reference levels are per-(ET, variable) pairs, and natural vs anthropogenic ETs take different
reference conditions. GLOBIO MSA is the happy case — an undisturbed reference is baked in. Most
variables are not. For those, the tractable methods from Table 5.9 at global scale are **statistical
approaches based on ambient distributions** (e.g. the 95th percentile of the variable within the same
ecoregion × ET as the upper reference level) and **prescribed levels**. Both are defensible if declared.

Store reference levels as a versioned lookup keyed by (ET, variable, source-of-reference), default to
ecoregion-percentile, and let the user override. Never average condition across ETs with different
reference conditions — the standard forbids it, and the agent must know that.

### 5.4 Scale honesty

Global land cover at 100–300 m, hexed at the catalog's res-8 convention (~74 ha per BSU), cannot support a
credible account for a 50-hectare farm. A defensible global EAA floor is nearer **50–100 km²** than the
10 km² an earlier draft of this document assumed; CONUS NLCD at res 10 (~1.5 ha) allows much finer work.
A minimum-area guard belongs in the system prompt, and it should be resolution-aware rather than a single
constant.

UNSD's tier framework says the same thing in its own vocabulary: property-boundary land-use planning is
**Tier 3**, and a global-data system is **Tier 1** — fit for "order of magnitude" estimates and
"awareness raising", not parcel decisions. See [`DATA.md`](DATA.md) §1.

### 5.5 Infrastructure note

Live validation of the extent-account SQL is **pending**: the NRP Ceph object store behind
`duckdb-mcp.nrp-nautilus.io` was returning `Timeout`/`Could not connect` on all bucket LIST and GET
operations during this scoping session (2026-07-30). DuckDB compute and H3 functions verified working
(`h3_cell_area`, `h3_latlng_to_cell` confirmed); only S3 access was down. The prototype queries in §10
should be run as the first task once it recovers, since they establish the performance budget the whole
interaction model assumes.

---

## 6. What the app does

### 6.1 Architecture: config over the geo-agent runtime

Fork `geo-agent-template`, following `landscape-frontiers`. Three files, no JavaScript:

- **`layers-input.json`** — collections (GET, land cover, GLOBIO, carbon, WDPA, Overture, HydroBASINS,
  population), `draw_enabled: true`, `charts.enabled: true`, global view, welcome examples.
- **`system-prompt.md`** — the SEEA framing the tools cannot supply: the five accounts, the ECT, the
  reference list, final-vs-intermediate discipline, aggregation rules (densities → AVG, stocks/areas →
  SUM), the reference-level and valuation-assumption protocol, and the minimum-area guard.
- **`k8s/`** — nginx + lab LLM proxy, per the standard two-target deploy (GitHub Pages BYO-key, or NRP).

Reference tables that must not drift — the GET↔land-cover crosswalk, reference levels, valuation
coefficients — live as **versioned data in-repo or in the catalog**, not as prose in the system prompt.
The agent reads them; it does not remember them.

### 6.2 The interaction loop

1. **Delimit the EAA** — draw, geocode, pick an admin unit / basin / protected area, or click a hex.
2. **Compile** — the agent runs the account chain, narrating each step and its assumptions:
   extent → condition → physical services → monetary services → asset account, ending in GEP.
3. **Inspect** — SEEA-structured tables, a map recoloured by ET / condition index / service supply, and
   charts (condition radar by ECT class, service supply by ET, asset value waterfall).
4. **Branch** — the user proposes a scenario. The accounts recompute and the *deltas* are presented in
   the standard's vocabulary.
5. **Export** — SEEA-conformant tables plus a methods-and-caveats record (matching ARIES's provenance
   bar) as XLSX/CSV.

### 6.3 The scenario mechanism

This is the differentiator, and it is a small change to a big machine — which is why it is worth doing.

A scenario is a **hypothetical reassignment of ET for a set of BSUs**: convert the drawn polygon's
forest to cropland; restore cropland to wetland; extend protection over these cells. It propagates
through the accounts exactly as SEEALand's single forest→cropland conversion does:

| Account | What the scenario changes |
|---|---|
| Extent | Managed expansion / managed reduction entries; a populated ET change matrix |
| Condition | Landscape-level (C1) variables recompute over changed neighbourhoods — the mechanism that drove SEEALand's forest decline. Structural/compositional variables shift to the new ET's expected values |
| Services (physical) | Per-ET service supply coefficients reapply to the new ET areas |
| Services (monetary) | Physical deltas × exchange prices |
| Asset | Expected future flows revise → **degradation** or **enhancement**, plus **conversion** entries, decomposed per Annex 10.1 |

The headline output is a sentence like: *"Converting 2 400 ha of T1.1 lowland rainforest to T7.1 annual
cropland raises crop provisioning by $1.9 M/yr, reduces global climate regulation by 310 kt CO₂, and
books $47 M of ecosystem degradation against a $12 M gain in cropland asset value."* That is the SEEA
framework doing the thing it was designed for, on the user's own proposal, in seconds.

Per-ET service coefficients and condition expectations are the scenario engine's parameters. Deriving
them empirically — the observed mean service supply per ET per ecoregion, straight from the accounts we
just compiled — keeps the scenario internally consistent with the baseline, and is itself one SQL query.

### 6.4 Where the runtime will fight us

- **Table-shaped output.** SEEA accounts are 2-D `entries × ET` tables with subtotals. The agent can
  emit markdown, which is probably adequate, but XLSX export is a hard requirement for statistical-office
  users and does not exist in the runtime today. Flag upstream.
- **Assumptions panel.** Discount rate, asset life, carbon price and reference-condition choice want to
  be persistent visible controls, not chat turns. This is the same *reactive-parameter* need
  landscape-frontiers logged for its weight slider (geo-agent #147); worth pooling into one upstream ask.
- **Arithmetic integrity.** Accounts must add up. An LLM transcribing numbers between tables will
  eventually not. Every account should be produced by a single SQL query whose output *is* the table —
  the agent narrates and never re-types figures.

---

## 7. Plan

**Phase 0 — validate the primitives (days).** Run the §10 prototype SQL once the object store is back:
fractional extent account for a country EAA; GLOBIO condition rollup; an NLCD two-year change matrix
for a CONUS basin. Establish the latency budget. Confirm `frac`-weighted areas reconcile against an
independent country-area figure.

**Phase 1 — replicate SEEALand (weeks).** Reproduce the annex end to end — six ETs, one conversion,
all five accounts, GEP $83,125 — as a fixture test with SEEALand's own numbers. This is the cheapest
possible proof that our account arithmetic and NPV decomposition are correct, before any real data
enters. It also becomes the regression test for the scenario engine, since SEEALand *is* a scenario.

**Phase 2 — CONUS vertical slice (weeks).** Annual NLCD gives real opening/closing extent today. Build
the full five-account chain for a US watershed: extent + change matrix, condition using GLOBIO + gHM +
computed C1 landscape metrics, physical services for the subset we can defend, monetary with the
assumptions panel, asset account with decomposition. Ship the scenario branch here.

**Phase 3 — go global (gated on ingest #1 and #2).** GLC_FCS30D and IUCN GET land in the catalog; the
crosswalk and reference-level tables get written and reviewed; the same app becomes any-AOI worldwide
with real change accounting.

**Phase 4 — validate against the world.** Compare against ARIES for SEEA on the same AOI and the same
accounts, and against published national compilations. Candidate replication targets, in order of
tractability: **Uganda** (UBOS/UNEP-WCMC experimental extent + species accounts — land-cover-based, so
closest to what we compute), **Netherlands** (annual, mature, well-documented — the hardest test),
**Costa Rica**, **Colombia**, **Mexico** (INEGI), **Brazil** (IBGE land-cover accounts every two
years). Publish the divergences.

Phases 1 and 2 need no new ingest and no new runtime features. That ordering is deliberate: it front-loads
the correctness work, which is where this project's credibility lives, and keeps the ambitious global
scope behind a gate we can see.

---

## 8. Open questions

1. **Who reviews the WTE→GET crosswalk?** It is the load-bearing ecological judgement in the whole design
   (§5.1) and should carry a named reviewer. Follow the **#427** precedent.
2. **Is a statistical office a target user?** If yes, XLSX export and a formal methods record move from
   nice-to-have to blocking, and the valuation guardrails (§5.2) need to be tighter than a research demo
   would require.
3. **Do we coordinate with the ARIES/UNSD team?** Validating against ARIES is far more valuable as
   collaboration than as an unannounced comparison, and they own the crosswalk problem too. UNEP-WCMC is
   the single contact that covers ARIES, ENCORE and WDPA at once ([`DATA.md`](DATA.md) §2.1).
4. **Commercial posture.** Several strong sources are NC (`gfw`, `public-carbon`, BII, Sea Around Us) or
   no-redistribution (WDPA, IUCN Red List, HydroSHEDS v1c). This gates the marine vertical and the
   protected-area accounts. See [`DATA.md`](DATA.md) §2.1, §5.1.
5. **Marine and transitional realms — lead or defer?** ARIES is terrestrial-only and the queued marine
   layers (#443 mangroves, #444 coral/seagrass) plus MEOW/GEBCO would make coastal-protection and
   wild-fish accounts genuinely novel — but the best marine provisioning sources are NC-restricted, so
   this depends on question 4.
6. **Ten services, or fewer done better?** [`DATA.md`](DATA.md) §5 commits to UNSD Chapter 6's ten, which
   is a superset of ARIES's four. A tighter v1 is those four plus erosion control — matching ARIES exactly
   makes head-to-head validation clean, with breadth added afterwards.
7. **Where do the non-spatial economic datasets live?** EXIOBASE/ESVD/ENCORE are national and sectoral
   lookup tables, not hexed rasters, so `data-workflows` may be the wrong home ([`DATA.md`](DATA.md) §7.2).

---

## 9. Provenance

- SEEA EA (2021) White Cover, 393 pp — `https://seea.un.org/sites/seea.un.org/files/documents/EA/seea_ea_white_cover_final.pdf`.
  Structural detail, table layouts, the ES reference list, the ECT, and the SEEALand annex in this
  document are taken from the extracted full text; see [`research/`](research/).
- SEEA EA methodology hub — `https://seea.un.org/en/methodology/ecosystem-accounting`
- ARIES for SEEA — `https://seea.un.org/en/data/aries-for-seea`, user guide at
  `https://aries.integratedmodelling.org/aries-for-seea-user-guide/`
- IUCN GET Level 3 v2.1 indicative maps — [Zenodo 10081251](https://zenodo.org/records/10081251), CC-BY
- GLC_FCS30D — [ESSD 16:1353 (2024)](https://essd.copernicus.org/articles/16/1353/2024/)
- Pattern precedent: [`landscape-frontiers`](https://github.com/boettiger-lab/landscape-frontiers) DESIGN.md

---

## 10. Appendix: Phase 0 prototype SQL

**Not yet executed** — the object store was down during scoping (§5.5). These are written against schemas
confirmed via `get_stac_details`, but treat them as unvalidated drafts: run them first, fix them, then
record the latencies. Always re-read exact S3 paths from `get_stac_details` rather than trusting the
paths inlined here.

**A note on partition pruning.** Globbing `h0=*` across a global res-9 fractional layer is the expensive
path, and the bucket LIST it requires is what was timing out. Constrain `h0` explicitly. Get the base
cells for an AOI with:

```sql
SELECT DISTINCT CAST(h3_latlng_to_cell(lat, lon, 0) AS BIGINT) AS h0
FROM (VALUES (8.0,-83.0),(11.2,-85.9),(10.0,-84.0),(9.0,-82.6)) AS t(lat,lon);
-- Costa Rica → {578290339652042751, 578395892768309247}
```

### A. Ecosystem extent account, single time point

Exact per-class area over an EAA, from fractional coverage. The `frac × cell_area` product is the
primitive the whole extent account rests on — validate it by reconciling the total against an
independent country-area figure.

```sql
WITH aoi AS (
  SELECT DISTINCT h8
  FROM read_parquet('s3://public-overturemaps/2026-02-18.0/countries/hex/h0=*/data_0.parquet')
  WHERE h0 IN (578290339652042751, 578395892768309247)
    AND country = 'CR' AND class = 'land'
)
SELECT f.lc_class,
       ROUND(SUM(f.frac * h3_cell_area(f.h9, 'km^2')), 1) AS area_km2,
       ROUND(100.0 * SUM(f.frac * h3_cell_area(f.h9, 'km^2'))
             / SUM(SUM(f.frac * h3_cell_area(f.h9, 'km^2'))) OVER (), 2) AS pct_of_eaa
FROM read_parquet('s3://public-land-cover/cgls-lc100-2019/hex-fractions/h0=*/data_0.parquet') f
SEMI JOIN aoi a ON f.h8 = a.h8
WHERE f.h0 IN (578290339652042751, 578395892768309247)
  AND f.lc_class NOT IN (0, 255, 200)   -- no-data, nodata sentinel, open sea
GROUP BY f.lc_class
ORDER BY area_km2 DESC;
```

### B. ET change matrix, two time points (CONUS, annual NLCD)

The pattern that unblocks the extent account's additions/reductions entries. Requires two NLCD years
hexed; only 2024 is currently in the catalog, so this is the query that motivates ingest #1 globally and
a second NLCD year for CONUS.

```sql
-- opening and closing dominant class per BSU, then the from→to matrix
WITH t0 AS (SELECT h10, nlcd AS et_open  FROM read_parquet('…/nlcd-<YEAR0>/hex/h0=*/data_0.parquet') WHERE h0 IN (…)),
     t1 AS (SELECT h10, nlcd AS et_close FROM read_parquet('…/nlcd-<YEAR1>/hex/h0=*/data_0.parquet') WHERE h0 IN (…)),
     aoi AS (SELECT DISTINCT h10 FROM … /* EAA hexes: WBD HUC, county, or drawn polygon */)
SELECT et_open, et_close,
       ROUND(SUM(h3_cell_area(t0.h10, 'km^2')), 2) AS area_km2
FROM t0 JOIN t1 USING (h10) SEMI JOIN aoi USING (h10)
GROUP BY et_open, et_close
ORDER BY area_km2 DESC;
```

Diagonal (`et_open = et_close`) is unchanged area; off-diagonal cells populate managed/unmanaged
expansion and reduction. Note this uses the **mode** asset, not fractions — a change matrix needs one
class per BSU on both dates. Sub-cell fractional change is a harder problem; res 10 (~1.5 ha) keeps the
mode assumption defensible for CONUS.

### C. Condition indicator, GLOBIO MSA

The happy case: MSA is already in [0,1] against an undisturbed reference, so the variable → indicator
step is the identity and no reference-level lookup is needed. Note the reducer — MSA is a bounded
intensity index, so **area-weighted mean, never sum**.

```sql
WITH aoi AS (SELECT DISTINCT h8 FROM … WHERE country = 'CR' AND class = 'land')
SELECT ROUND(SUM(g.msa * h3_cell_area(g.h8, 'km^2')) / SUM(h3_cell_area(g.h8, 'km^2')), 4) AS msa_indicator,
       ROUND(SUM(h3_cell_area(g.h8, 'km^2')), 1) AS area_km2
FROM read_parquet('s3://public-globio/globio-msa-2015-overall/hex/h0=*/data_0.parquet') g
SEMI JOIN aoi a ON g.h8 = a.h8
WHERE g.h0 IN (…);
```

Break this out **by ET** (join to land cover on `h8`) to get the per-ET condition the account requires —
and remember §5.3: do not then average across ETs.

### D. Condition C1 landscape metrics — the differentiator

Forest area density over a k-ring, straight from hex land cover. This is the variable that carries
SEEALand's forest condition decline, and the reason the scenario engine works.

```sql
WITH forest AS (   -- forest fraction per BSU (LCCS closed+open forest classes)
  SELECT h9, SUM(frac) AS forest_frac
  FROM read_parquet('s3://public-land-cover/cgls-lc100-2019/hex-fractions/h0=*/data_0.parquet')
  WHERE h0 IN (…) AND lc_class BETWEEN 111 AND 126
  GROUP BY h9
),
nbr AS (           -- k-ring neighbourhood of each cell
  SELECT f.h9 AS focal, UNNEST(h3_grid_disk(f.h9, 3)) AS neighbour FROM forest f
)
SELECT n.focal,
       AVG(COALESCE(f2.forest_frac, 0)) AS forest_area_density
FROM nbr n LEFT JOIN forest f2 ON f2.h9 = n.neighbour
GROUP BY n.focal;
```

Same shape gives fragmentation (share of neighbours in a different class) and landscape diversity
(Shannon entropy over neighbourhood class fractions). **Validate the cost of this one carefully** — the
`h3_grid_disk` unnest multiplies row count by the k-ring size (k=3 → 37×), so it is the most likely
performance surprise in the whole design, and the k that stays interactive sets a real design constraint.

### E. Global climate regulation, physical

Carbon stock (retention) over the EAA. `carbon` is a per-cell **total**, so `SUM` is correct here — the
opposite of the MSA rule above, and the aggregation trap the system prompt must state explicitly.

```sql
SELECT ROUND(SUM(c.carbon) / 1e6, 2) AS mt_carbon
FROM read_parquet('s3://public-carbon/…/hex/h0=*/data_0.parquet') c
SEMI JOIN aoi a ON h3_cell_to_parent(c.h9, 8) = a.h8
WHERE c.h0 IN (…);
```

The sequestration *flow* half of this service needs ingest #3.
