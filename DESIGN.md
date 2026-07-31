# unseea — a UN SEEA-EA decision planning tool on the geo-agent runtime

**Status:** scoping design document. No code yet.
**Sources:** SEEA EA, **official 2024 edition** (ST/ESA/STAT/SER.F/124, 443 pp) — full text extracted; ARIES for SEEA
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
> asset)." — SEEA EA (2024 official ed.), Annex I, Table AI.5, footnote c

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

> "An average measure of ecosystem condition across all ecosystem types has not been derived, as this
> would imply aggregation across different reference conditions, which is not recommended."

Design consequence: reference levels must be an explicit, inspectable, user-overridable object in this
app, not a hidden constant. This is where an agent earns its place — it can *explain* which reference
condition was assumed and let the user change it. See §5.3 for the sensitivity requirement this implies.

#### ⚠️ Weight dilution: "present but not measured" silently reweights the index

The index weights are not arbitrary. Checked against all six SEEALand ecosystem types, the rule is
**one equal vote per ECT class *present*, then split equally among the variables inside that class.**
Forest's abiotic ⅓ / biotic ½ / landscape ⅙ is just 2, 3 and 1 classes each taking ⅙.

The load-bearing word is *present*. **SEEALand's urban area has no B3 functional variable, so its five
classes are weighted 0.20 each rather than 0.167.** The consequence is a real methodological hazard:

> An ECT class you cannot measure does not contribute zero — it contributes *nothing*, and every class
> you **can** measure silently gains weight. Two analysts with different data coverage produce different
> condition indices for the same ecosystem, in the same units, with no indication that they differ.

This bites us hard, because our layer coverage is uneven by ECT class (§2.4 table vs `PROVENANCE.md` §3)
and will stay uneven for some time. Two ecosystem types compiled from different numbers of ECT classes
are **not comparable**, even though both indices are dimensionless and in [0,1].

Design consequences, all mandatory:

- Record **which ECT classes were populated** alongside every condition index, and surface it in the UI —
  an index built from 3 of 6 classes must be visibly labelled as such.
- **Never compare condition indices across ETs, areas or time points with different ECT coverage** without
  restating both on the common subset of classes.
- Offer **"recompute on the intersecting classes"** as a first-class operation whenever two condition
  indices are placed side by side. This is the condition-account analogue of the density-vs-amount rule:
  cheap to implement, and silently wrong if omitted.
- The agent must state ECT coverage whenever it reports a condition index, exactly as it must state the
  discount rate before reporting an asset value (§5.2).

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

**Measured, and the claim holds.** Forest area density over a country EAA runs in 3.4 s at `k=3` and
5.8 s at `k=10`; increasing `k` from 1 to 40 multiplies row count by 700× but wall clock by only 9×
(§10.2). The cost is the parquet scan, not the neighbourhood expansion — so the metric family really is
close to free, and the practical limit is EAA size rather than `k` (§10.3).

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

#### Reference-level sensitivity is a headline feature, not a diagnostic

Because no reference level is canonical, the honest product is not one number but **the response of the
account to how the reference is defined.** Being fast and reproducible is what makes that possible, and it
is a genuine differentiator: published compilations pick one reference basis and report it, because
recompiling is expensive. For us recompiling is seconds (§10.1).

Requirements:

- Reference levels are a **first-class user input**, settable three ways: chosen from the versioned
  defaults we ship, derived from a layer we have processed (ecoregion percentiles, reference sites), or
  **supplied directly by the user** — including partners with better local knowledge than any global layer.
- Every condition and monetary output carries the reference set that produced it, and any two results can
  be diffed.
- The UI should make **sweeping** a reference basis as easy as picking one, and show the account's
  sensitivity to it.

**One analytical result worth encoding, because it tells users which sensitivity actually matters.** Under
the linear rescaling SEEALand uses, `indicator = (x − lower) / (upper − lower)`, so for two scenarios A
and B measured on the same variable:

```
indicator_A − indicator_B = (x_A − x_B) / (upper − lower)
```

The difference is **invariant to where the reference is anchored** (`lower` cancels) and **scales inversely
with the width of the reference range**. So:

- Moving a reference level up or down changes every *level* but **cannot reorder two scenarios**.
- Narrowing or widening the reference *range* rescales the magnitude of all differences — it changes how
  big the gap looks, not its sign.
- **Only a non-linear rescaling can reorder scenarios.** SEEA permits non-linear rescaling where the
  ecological response is non-linear, so linear-vs-non-linear is the choice that genuinely carries
  ranking risk, and it deserves far more prominence than nudging a bound.

That is a much sharper thing to tell a user than "results are sensitive to reference levels", and it means
scenario *comparisons* are considerably more robust than scenario *levels* — which is fortunate, because
comparison is what decisions need.

### 5.4 Scenarios are not accounts, and reference levels are not counterfactuals

The most common way a partner will want to use this tool is to compare land-use options — a lower-impact
production practice against a more intensive one. That is legitimate and well within SEEA's reach, but it
requires keeping two things apart that are easily conflated:

| | What it is | Where it lives | Status |
|---|---|---|---|
| **Reference level** | The [0,1] rescaling anchor. Defines what *good condition* means for an ecosystem type | Inside the condition account, stage 2b | ✅ **Explicitly sanctioned**, several bases permitted |
| **Counterfactual baseline** | "Compared to what would otherwise have happened" | Outside the accounts entirely | ⚠️ **Not an accounting entry** |

"Baseline" in ordinary speech usually means the second. In SEEA it is almost always the first — and the
first is where the nuance a partner wants actually belongs.

**What is compatible.** An account may use an *anthropogenic* reference level: for an agricultural
ecosystem type, lower reference = the most degraded prevailing practice, upper = best attainable. A
lower-impact system then scores high condition without anyone pretending it is primary forest. This is
what SEEALand itself does for cropland — see the next subsection.

**What is not.** Three hard walls, worth stating because partners will ask for all three:

1. **"Avoided degradation" is not an accounting entry.** The monetary asset account's lines are opening,
   enhancement, degradation, conversions, other volume changes, reappraisals, revaluations, closing.
   There is **no avoided-loss line**. "Practice A prevented the conversion that would otherwise have
   happened, so credit it with the averted damage" cannot be posted. The compatible way to answer the
   same question is to compile **both scenarios' full accounts** and present the pair plus their
   difference — the counterfactual then lives visibly in the framing rather than smuggled into a ledger.
2. **No single landscape condition score.** Condition cannot be averaged across ecosystem types with
   different reference conditions (§5.3). Results are reported per ET, always.
3. **An account records an actual period.** Forward-looking comparison is an *application* of the
   machinery, not an account. Label such outputs scenario projections. Cheap to honour, and it is the
   difference between credible and not when a statistical agency reads the output.

**The classification choice decides the accounting entry.** Whether a modified system is filed as the
same ecosystem type in poorer condition, or as a *different* ecosystem type, determines whether the
change posts as **degradation** or as **conversion** — same ecology, different ledger. This is a
declarable methodological choice with large consequences, and the tool must surface it rather than bury
it.

#### Working lands: the standard already scores agricultural practice

This is a stronger precedent than we expected, and it is the citation that makes working-lands
applications defensible. SEEALand's own **cropland** condition variables are, verbatim:

| ECT class | Cropland variable |
|---|---|
| A1 physical | Vegetation water content |
| A2 chemical | Soil organic carbon |
| B1 compositional | **Farmland bird species richness** |
| B2 structural | **Crop diversity** · **Share of organic farming** |
| B3 functional | Gross primary production |
| C1 landscape | **Share of semi-natural vegetation** |

The standard's own worked example scores agricultural condition using organic-farming share, crop
diversity, farmland bird richness and semi-natural vegetation share, against an **anthropogenic**
reference level. Distinguishing a lower-impact production system from an intensive one on canopy
retention, native species presence and surrounding semi-natural cover is therefore **not a stretch of
SEEA — it is the pattern SEEALand demonstrates**, applied to a different crop.

Consequences for us:

- Practice differentiation is a **data gap, not a framework gap**. What is missing is
  practice-differentiated land cover and **practice-response coefficients** (practice → expected
  condition-variable values). Nothing in the catalog supplies either; our layers are *observed
  baselines*, not response functions.
- Response coefficients are a **general gap class**, not an application detail — any scenario on any
  managed system needs them. They belong on the roadmap as a first-class artifact type
  ([`ARCHITECTURE.md`](ARCHITECTURE.md), parameter sets).
- IUCN GET's T7 intensive-land-use biome (T7.1 annual croplands, T7.2 sown pastures, T7.3 plantations,
  T7.4 urban/industrial, T7.5 derived semi-natural pastures) is the right home, and SEEA permits finer
  national sub-classifications that crosswalk to GET. Sub-dividing T7.3 by practice is compatible.
- Direct measurement — acoustic monitoring, eDNA — slots into **B1 compositional** with no framework
  friction. SEEA is method-agnostic about how a variable is measured; it requires only that the variable
  be rescaled against a declared reference. These measure the same construct as MSA, more directly.
- The honest risk is not compatibility, it is that **anthropogenic reference levels for most production
  systems do not exist and we would be inventing them.** Defensible if declared — the standard permits
  prescribed levels and expert opinion — but it is where review will push hardest, and precisely why the
  sensitivity sweep in §5.3 matters. Better to show a result holds across the plausible reference range
  than to pick one and defend it.

### 5.5 Scale honesty

Global land cover at 100–300 m, hexed at the catalog's res-8 convention (~74 ha per BSU), cannot support a
credible account for a 50-hectare farm. A defensible global EAA floor is nearer **50–100 km²** than the
10 km² an earlier draft of this document assumed; CONUS NLCD at res 10 (~1.5 ha) allows much finer work.
A minimum-area guard belongs in the system prompt, and it should be resolution-aware rather than a single
constant.

UNSD's tier framework says the same thing in its own vocabulary: property-boundary land-use planning is
**Tier 3**, and a global-data system is **Tier 1** — fit for "order of magnitude" estimates and
"awareness raising", not parcel decisions. See [`DATA.md`](DATA.md) §1.

### 5.6 Infrastructure: use the mirror, don't wait on the primary

The NRP Ceph object store behind `duckdb-mcp.nrp-nautilus.io` is not reliably available — it was fully
down during scoping (2026-07-30) and still recovering the next day. **This is not a reason to block work**,
because the catalog has a drop-in read mirror.

**MinIO mirror** — `minio.carlboettiger.info`, same bucket names, same catalog structure, anonymous reads
([failover guide](https://boettiger-lab.github.io/mcp-data-server/guide/mirror-failover.html)). Route a
query to it by passing the endpoint plus a scope:

```
s3_endpoint = 'minio.carlboettiger.info'
s3_scope    = 's3://public-land-cover'      -- per bucket; confines the endpoint to that prefix
```

⚠️ **Always pass `s3_scope`.** A bare `s3_endpoint` applies to *every* `s3://` path in the query and
disables the server default, which silently breaks any query mixing buckets.

**Verified 2026-07-31:** the fractional-extent primitive returns byte-identical results from the mirror and
from the primary. The primary had recovered later that day, and the full Phase 0 run (§10) executed
against it. Design consequences:

- Phase 0 (#2) and everything downstream can proceed against the mirror.
- The app should treat the mirror as a **first-class fallback**, not an emergency measure. Since a SEEA
  account is a reconciling table, a partial read is worse than a failed one — an account that silently
  omits a bucket still *looks* balanced. Prefer failing over to failing quietly.
- Map layers (PMTiles, COGs) are fetched client-side, so a full failover also needs the host swapped in
  `layers-input.json` — a separate change from the SQL path (#11).

---

## 6. What the app does

### 6.1 Architecture: config over the runtime, plus the account library

**See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full treatment.**

The `geo-agent-template` pattern stands: fork it, three files, no JavaScript.

- **`layers-input.json`** — collections (GET, land cover, GLOBIO, carbon, WDPA, Overture, HydroBASINS,
  population), `draw_enabled: true`, `charts.enabled: true`, global view, welcome examples.
- **`system-prompt.md`** — the SEEA framing the tools cannot supply: the five accounts, the ECT, the
  reference list, final-vs-intermediate discipline, aggregation rules (densities → AVG, stocks/areas →
  SUM), the reference-level and valuation-assumption protocol, ECT-coverage disclosure (§2.4), and the
  minimum-area guard.
- **`k8s/`** — nginx + lab LLM proxy, per the standard two-target deploy (GitHub Pages BYO-key, or NRP).

**One addition, and it is the only thing unseea contributes as machinery:** a **Python library
implementing the five accounts behind a narrow API**, with a pluggable executor and an optional MCP
endpoint. Nine calls — `connect`, `eaa`, and one per account — because SEEA fixed the surface for us.

The API takes structured parameters and returns the account **plus the exact SQL it ran**:

```python
acct = eng.extent_account(eng.eaa(country="CR"), date=2019)
acct.table   # the SEEA-shaped table       acct.checks       # reconciliation results
acct.sql     # re-runnable in any DuckDB   acct.provenance   # bindings, parameters, ECT coverage, licences
```

> **SQL is not the interface. It is the returned artifact.**

The reason is narrow and worth stating precisely, because it is easy to overstate. `geo-agent`'s chat
export already gives **session reproducibility** — every `s3://` in an exported SQL block is rewritten to
`https://s3-west.nrp-nautilus.io/…`, so it re-runs in any DuckDB with `httpfs` and no credentials. What
it cannot give is **specification conformance**: nothing makes two sessions compile the *same* account,
and the SEEALand fixture can only test a fixed definition. A statistical standard needs both properties,
and returning `acct.sql` gets both rather than trading one for the other.

The executor is where the runtime choice lives — the deployed `mcp-data-server`, a local DuckDB against
NRP or source.coop, or a **fixture executor with no network at all**, which is what makes Phase 1
testable before any layer is trusted.

Everything else is reuse, deliberately:

| Layer | Component | Owner |
|---|---|---|
| Data | `data-workflows` → the h3-stac catalog | upstream |
| **Engine** | **`mcp-data-server`** — DuckDB, STAC grounding, H3, private routing, mirror failover | upstream |
| App shell | `geo-agent` — map, chat, agent loop, reproducible export | upstream |
| **Accounts** | **this repo** — SQL, manifests, bindings, parameter sets, vocabularies | unseea |
| Applications | own bindings and parameter sets, private data by credential | separate repos |

**The engine stays upstream.** `mcp-data-server` is deliberately domain-agnostic — its roadmap is engines
and data types, not domain semantics — so SEEA logic is an unseea artifact and engine needs go upstream
rather than into a fork. Serving the library as its *own* MCP endpoint is composition, not a fork, and is
what makes the narrow API reachable from every client; it needs one small upstream change, since
`geo-agent` takes a single `mcp_url` today. **Build the library first** — all the risk is in the API and
the arithmetic, and neither needs a deployment to test.

**We are testing this, not asserting it.** Two arms get built and scored in `geo-agent-benchmark`:
**A**, the narrow API; **B**, worked SQL in the system prompt with the agent writing account SQL itself.
Arm B is more flexible and more error-prone, and the gap should narrow as models improve — which is why
it needs measuring. SEEALand gold sits at **L3** on that benchmark's provenance ladder by construction,
matching a published professional source with tolerance. The property to watch is **run-to-run variance
on identical questions**, which Arm B structurally cannot guarantee.

Two rules carry the design:

> **If an application requires a change to the account SQL, the abstraction is wrong.** Applications add
> bindings, parameter sets, vocabularies and data.

> **The agent selects and parameterizes account compilations. It does not author account arithmetic.**
> Exploratory SQL stays fully available, as a visibly different class of work.

Reference tables that must not drift — the GET↔land-cover crosswalk, reference levels, valuation
coefficients — are **versioned data artifacts**, in-repo or in the catalog, never prose in the system
prompt. The agent reads them; it does not remember them.

The validated SQL in §10 is the first draft of the account library, not a throwaway prototype. Prior art
for the shape: `boettiger-lab/wyoming` carries a fixed reference analysis as `run_fixed_analysis.sql`,
validated against an independent R implementation.

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

**Partly superseded by §6.1.** Arithmetic integrity largely dissolves once accounts come from versioned
SQL rather than being re-derived per session: it becomes a property test on a fixed definition
([`ARCHITECTURE.md`](ARCHITECTURE.md)), and the output schema is fixed by the standard. Two frictions
survive and are worth pooling into one upstream ask: **XLSX export** (the chat export is excellent HTML,
but statistical-office users need spreadsheets) and the **assumptions panel** — reactive parameters
remain a real runtime gap, shared with landscape-frontiers' weight slider (geo-agent #147).

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

**Phase 0 — validate the primitives (days). ✅ Done 2026-07-31, except the change matrix.** The extent,
condition, landscape-metric and carbon primitives all run and reconcile; `frac`-weighted areas close to
−0.2% against an independent country-area figure at Costa Rica scale and within −1.2% out to Brazil. Every
account is interactive (3–10 s) for a country-sized EAA. The k-ring landscape metric turned out **not** to
be the performance risk the design assumed — `k` is nearly free, and EAA size is what binds, with a hard
~100 s gateway ceiling at continental scale. Full results, corrected SQL and the latency budget: §10.
The NLCD two-year change matrix remains blocked on a second CONUS year (data-workflows#453).

**Phase 1 — write the account library, with SEEALand as its spec (weeks).** Not "write a fixture test" —
**write the library**, using the annex as the specification: six ETs, one conversion, all five accounts,
GEP $83,125, forest ΔNPV −$116,366. Same work as the earlier framing, but the artifact is reusable rather
than a test script.

This is the phase where the seam gets fixed ([`ARCHITECTURE.md`](ARCHITECTURE.md)): the nine-call API,
the executor split, the binding/parameter/vocabulary separation, licence propagation, and the three test
tiers. SEEALand is the ideal spec precisely because it has **no data dependency** — the fixture executor
needs no network, so the arithmetic and the NPV decomposition are forced correct before any layer is
trusted. It then stays as the conformance test, and as the regression test for the scenario engine, since
SEEALand *is* a scenario.

Runs in parallel, and gates the design ([#28](https://github.com/SchmidtDSE/unseea/issues/28)): **build
Arm B too** — the system-prompt-plus-worked-SQL variant — and score both in `geo-agent-benchmark`. If Arm
B matches Arm A on accuracy *and* on run-to-run variance, the library is not earning its keep and we
should say so. Tracked: library [#27](https://github.com/SchmidtDSE/unseea/issues/27), evaluation
[#28](https://github.com/SchmidtDSE/unseea/issues/28), MCP endpoint
[#29](https://github.com/SchmidtDSE/unseea/issues/29).

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

- SEEA EA, **official 2024 edition** — ST/ESA/STAT/SER.F/124, 443 pp, `https://seea.un.org/sites/default/files/documents/EA/seea_ea_f124_web_12dec24.pdf` (the 2021 White Cover is also retained for reference).
  Structural detail, table layouts, the ES reference list, the ECT, and the SEEALand annex in this
  document are taken from the extracted full text; see [`research/`](research/).
- SEEA EA methodology hub — `https://seea.un.org/en/methodology/ecosystem-accounting`
- ARIES for SEEA — `https://seea.un.org/en/data/aries-for-seea`, user guide at
  `https://aries.integratedmodelling.org/aries-for-seea-user-guide/`
- IUCN GET Level 3 v2.1 indicative maps — [Zenodo 10081251](https://zenodo.org/records/10081251), CC-BY
- GLC_FCS30D — [ESSD 16:1353 (2024)](https://essd.copernicus.org/articles/16/1353/2024/)
- Pattern precedent: [`landscape-frontiers`](https://github.com/boettiger-lab/landscape-frontiers) DESIGN.md

---


## 10. Appendix: Phase 0 — validated primitives, measured

**Status: run and validated 2026-07-31** against the primary catalog (`s3-west.nrp-nautilus.io`), which
had recovered from the outage described in §5.6. Tasks **A, C, D and E pass**. Task **B remains blocked**
on a second NLCD year (boettiger-lab/data-workflows#453) — it is the only Phase 0 task with a data
dependency.

All timings below are wall-clock round trips through the MCP endpoint `duckdb-mcp.nrp-nautilus.io`,
median of three runs unless stated. They include HTTP and S3 latency, so they are what a user would
actually wait, not engine time.

Always re-read exact S3 paths from `get_stac_details` rather than trusting the paths inlined here.

### 10.1 Latency budget

Costa Rica EAA (51,181 km², 2 `h0` partitions, 109,055 res-8 cells) — the reference "country-scale"
accounting area.

| Task | Query | Median | Notes |
|---|---|---:|---|
| A | Extent account, per-class area | **4.3 s** | 13 classes returned |
| C1 | MSA condition indicator, whole EAA | **6.2 s** | both weightings in one query |
| C2 | MSA condition indicator by ET | **6.5 s** | the form the account actually needs |
| D | Landscape metrics, `k=3` | **3.4 s** | 404,240 focal cells, 15.0M unnest rows |
| E | Carbon stock total | **3.8 s** | 763,385 res-9 cells |
| E2 | Carbon by ET | **9.9 s** | res-9 ⋈ res-9 join, the most expensive of the five |

**Every account is interactive at country scale.** Nothing here needs precomputation or a materialised
cache for a Costa-Rica-sized EAA.

### 10.2 The `k` decision

**`k` is not the constraint the design feared.** Sweeping `k` over the Costa Rica EAA, with focal cells
held constant at 404,240:

| `k` | ring size | unnest rows | secs |
|---:|---:|---:|---:|
| 1 | 7 | 2.8M | 3.3 |
| 3 | 37 | 15.0M | 3.4 |
| 5 | 91 | 36.8M | 3.8 |
| 10 | 331 | 133.8M | 5.8 |
| 15 | 721 | 291.5M | 7.0 |
| 20 | 1,261 | 509.7M | 10.1 |
| 25 | 1,951 | 788.7M | 14.1 |
| 30 | 2,791 | 1,128M | 19.9 |
| 40 | 4,921 | 1,989M | 30.2 |

Row count grows **700×** from `k=1` to `k=40`; wall clock grows **9×**. The `h3_grid_disk` unnest is
cheap, and DuckDB's hash join over the neighbour table absorbs it well.

**Decision: `k ≤ 10` for interactive use, `k = 3` as the default** for forest area density. `k = 10` at
res 9 is a ~3.5 km neighbourhood radius, which is already generous for a landscape-context metric —
we run out of ecological justification long before we run out of compute. Larger `k` stays available for
offline or batch work up to the ceiling in §10.3.

### 10.3 What actually binds: EAA size

Holding `k = 3` and growing the accounting area:

| EAA | land km² | `h0` parts | focal cells | A: extent | D: `k=3` |
|---|---:|---:|---:|---:|---:|
| Costa Rica | 51,181 | 2 | 404,240 | 4.7 s | 3.4 s |
| Colombia | 1,138,460 | 4 | 8,768,300 | 5.6 s | 15.9 s |
| Peru | 1,292,090 | 4 | 6,982,320 | 6.7 s | 14.0 s |
| Brazil | 8,507,770 | 12 | 58,380,600 | 19.6 s | 85.3 s |

Unnest rows alone do **not** predict cost: Brazil at `k=3` is 2,160M rows in 84 s, while Costa Rica at
`k=40` is 1,989M rows in 30 s. The difference is the parquet scan across `h0` partitions. Isolating it on
the Brazil EAA:

| `k` | unnest rows | secs |
|---:|---:|---:|
| 1 | 409M | 24.7 |
| 3 | 2,160M | 84.2 |
| 6 | 7,414M | **fails at ~100 s** |

⚠️ **There is a hard operational ceiling near 100 seconds** — the request dies with a truncated read,
which is a gateway timeout rather than a query failure. Any account that might exceed it needs to be
chunked by `h0` or precomputed, not merely optimised.

**Design constraint, stated plainly.** Budget on `h0` partition count first and focal-cell count second;
`k` is nearly free. Continental EAAs (Brazil, CONUS, the EU) are the case that needs a different
execution strategy, and the scenario engine — which reruns landscape metrics on every edit — should
restrict recomputation to the edited neighbourhood rather than the whole EAA.

### 10.4 Two gotchas worth encoding in the system prompt

**1. `ST_Area_Spheroid` reads coordinates as (lat, lon), not (lon, lat).** On this DuckDB spatial build it
returns 5,323 km² for Costa Rica; wrapped in `ST_FlipCoordinates` it returns 51,181 km², which matches the
official ~51,100 km². Verified independently against a 1°×1° box. Any reference-area computation must
flip first, or every reconciliation silently "fails" by an order of magnitude.

**2. A res-8 EAA overshoots the coastline badly — and the fractional layer self-corrects it.** The
Overture countries hex for Costa Rica covers 80,891 km², 58% more than the country's 51,181 km². The
entire excess comes back from the land-cover join as class 200 (open sea): 29,393 km². Excluding classes
200, 80 and 0 recovers the true area to within 0.2%. **Do not "fix" the EAA by shrinking it** — the
fraction layer already carries the correct land share of every coastal cell.

### 10.5 Partition pruning

Globbing `h0=*` across a global res-9 fractional layer is the expensive path, and the bucket LIST it
requires is what was timing out during the outage. Constrain `h0` explicitly. Derive the base cells for an
AOI from its bounding box:

```sql
WITH c AS (
  SELECT bbox FROM read_parquet('s3://public-overturemaps/2026-02-18.0/countries.parquet')
  WHERE country = 'CR' AND class = 'land'
),
g AS (
  SELECT bbox.xmin + (bbox.xmax - bbox.xmin) * i / 24.0 AS lon,
         bbox.ymin + (bbox.ymax - bbox.ymin) * j / 24.0 AS lat
  FROM c, range(0, 25) t(i), range(0, 25) u(j)
)
SELECT DISTINCT CAST(h3_latlng_to_cell(lat, lon, 0) AS BIGINT) AS h0 FROM g;
-- Costa Rica → {578290339652042751, 578395892768309247}
```

A bbox grid over-covers (corners land in the ocean), which costs extra scan but never drops data. That
trade is correct: a missed `h0` silently truncates the account.

---

### A. Ecosystem extent account, single time point ✅

Exact per-class area over an EAA, from fractional coverage. The `frac × h3_cell_area()` product is the
primitive the whole extent account rests on.

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
  AND f.lc_class NOT IN (0, 200, 80, 255)   -- no-data, open sea, permanent water, nodata sentinel
GROUP BY f.lc_class
ORDER BY area_km2 DESC;
```

**The acceptance test passes, at four EAA scales**, against the spheroid area of the country's own
Overture land polygon (`ST_Area_Spheroid(ST_FlipCoordinates(geometry))`, §10.4):

| EAA | computed km² | polygon km² | error |
|---|---:|---:|---:|
| Costa Rica | 51,078 | 51,181 | **−0.20%** |
| Colombia | 1,132,660 | 1,138,460 | −0.51% |
| Peru | 1,283,050 | 1,292,090 | −0.70% |
| Brazil | 8,412,580 | 8,507,770 | −1.12% |

The residual is the res-9 discretisation of the coastline and drifts with the coast-to-area ratio, as it
should. **Areas close. Everything downstream is trustworthy.**

**Fractions vs. mode — the composition argument.** Both totals close (mode gives 51,043 km², −0.27%),
because coastal over- and under-counting cancels. Per class they do not:

| class | fractional km² | mode km² | mode error |
|---|---:|---:|---:|
| 112 Closed forest, evergreen broadleaf | 22,836 | 23,902 | +4.7% |
| 40 Cropland | 16,273 | 17,357 | +6.7% |
| 122 Open forest, evergreen broadleaf | 2,610 | 1,580 | **−39.5%** |
| 116 Closed forest, unknown | 802 | 275 | **−65.8%** |
| 20 Shrubs | 348 | 147 | **−57.6%** |
| 115 Closed forest, mixed | 15 | 1 | **−92.0%** |

Mode systematically erases minority classes into whichever class dominates each cell. An extent account
built on mode would show a plausible total and a badly wrong composition — and composition is the whole
account. **Use `hex-fractions` for extent; use `hex` (mode) only for map styling.**

### B. ET change matrix, two time points ⛔ blocked

The pattern that unblocks the extent account's additions/reductions entries. Requires two NLCD years
hexed; only 2024 is in the catalog, so this motivates a second CONUS year
(boettiger-lab/data-workflows#453) and global annual land cover (ingest #1).

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
mode assumption defensible for CONUS. Given task A's finding above, expect the mode assumption to distort
minority-class transitions; quantify that before trusting the off-diagonal entries.

### C. Condition indicator, GLOBIO MSA ✅

MSA is already in [0,1] against an undisturbed reference, so the variable → indicator step is the
identity and no reference-level lookup is needed. **MSA is a bounded intensity index: area-weighted mean,
never sum.**

The EAA's coastal overshoot matters here too. GLOBIO drops ocean cells, so the naive whole-cell weighting
is close — but the defensible form weights by *land* area from the fraction layer:

```sql
WITH aoi AS (
  SELECT DISTINCT h8
  FROM read_parquet('s3://public-overturemaps/2026-02-18.0/countries/hex/h0=*/data_0.parquet')
  WHERE h0 IN (578290339652042751, 578395892768309247)
    AND country = 'CR' AND class = 'land'
),
lc AS (   -- ET area within each h8, from sub-cell fractions
  SELECT h8, lc_class, SUM(frac * h3_cell_area(h9, 'km^2')) AS et_km2
  FROM read_parquet('s3://public-land-cover/cgls-lc100-2019/hex-fractions/h0=*/data_0.parquet')
  WHERE h0 IN (578290339652042751, 578395892768309247)
    AND lc_class NOT IN (0, 200, 80, 255)
  GROUP BY h8, lc_class
)
SELECT lc.lc_class,
       ROUND(SUM(g.msa * lc.et_km2) / SUM(lc.et_km2), 4) AS msa_by_et,
       ROUND(SUM(lc.et_km2), 1) AS et_area_km2
FROM lc
JOIN read_parquet('s3://public-globio/globio-msa-2015-overall/hex/h0=*/data_0.parquet') g
  ON g.h8 = lc.h8 AND g.h0 IN (578290339652042751, 578395892768309247)
SEMI JOIN aoi a ON lc.h8 = a.h8
GROUP BY lc.lc_class
ORDER BY et_area_km2 DESC;
```

Costa Rica, whole EAA: **MSA = 0.4122** land-weighted (0.4157 naive). The land-weighted denominator,
51,070 km², reconciles with task A's 51,078 km² — the 8 km² gap is cells where GLOBIO has no value.

By ET, the ordering is ecologically sensible, which is the real evidence the join is right:

| ET | MSA | area km² |
|---|---:|---:|
| 112 Closed forest, evergreen broadleaf | 0.544 | 22,835 |
| 90 Herbaceous wetland | 0.479 | 567 |
| 116 Closed forest, unknown | 0.448 | 802 |
| 126 Open forest, unknown | 0.345 | 6,225 |
| 30 Herbaceous vegetation | 0.280 | 706 |
| 40 Cropland | 0.266 | 16,273 |
| 50 Urban / built-up | 0.241 | 660 |

⚠️ **Scale caveat.** MSA is res 8 (~0.46 km²) while the ET fractions are res 9. Each h8 cell's single MSA
value is attributed to every ET present within it, so these per-ET figures carry the cell's mixed
landscape, not the ET's own intactness. Real, and worth stating in the methods record — see §5.5.

Per §5.3, report these per ET and **never average across them**: forest and cropland are scored against
different reference conditions.

### D. Condition C1 landscape metrics ✅

Forest area density over a k-ring, straight from hex land cover. This is the variable that carries
SEEALand's forest condition decline, and the reason the scenario engine works.

⚠️ **The draft of this query in earlier revisions was wrong**: it constrained `h0` but never joined the
EAA, so it silently computed all of Central America (17.7M focal cells) instead of Costa Rica (404k).
Constraining `h0` is a partition-pruning optimisation, **not** a spatial filter. The corrected form scores
only cells inside the EAA while keeping the neighbour universe unclipped, so k-rings that cross the EAA
boundary are not truncated:

```sql
WITH aoi AS (
  SELECT DISTINCT h8
  FROM read_parquet('s3://public-overturemaps/2026-02-18.0/countries/hex/h0=*/data_0.parquet')
  WHERE h0 IN (578290339652042751, 578395892768309247)
    AND country = 'CR' AND class = 'land'
),
forest AS (            -- neighbour universe: NOT clipped to the EAA, so no edge truncation
  SELECT h9, h8, SUM(frac) AS forest_frac
  FROM read_parquet('s3://public-land-cover/cgls-lc100-2019/hex-fractions/h0=*/data_0.parquet')
  WHERE h0 IN (578290339652042751, 578395892768309247)
    AND lc_class BETWEEN 111 AND 126
  GROUP BY h9, h8
),
focal AS (             -- but score only cells inside the EAA
  SELECT f.h9, f.forest_frac FROM forest f SEMI JOIN aoi a ON f.h8 = a.h8
),
nbr AS (
  SELECT f.h9 AS focal, UNNEST(h3_grid_disk(f.h9, 3)) AS neighbour FROM focal f
)
SELECT n.focal,
       AVG(COALESCE(f2.forest_frac, 0)) AS forest_area_density
FROM nbr n LEFT JOIN forest f2 ON f2.h9 = n.neighbour
GROUP BY n.focal;
```

Costa Rica, `k=3`: 404,240 forest cells, mean forest area density **0.724**, 41.6% of forest cells above
0.9 (interior/core forest). Mean density falls monotonically with `k` — 0.748 at `k=1` to 0.632 at `k=40` —
as the widening neighbourhood pulls in non-forest, which is exactly the behaviour a fragmentation metric
should show.

Same shape gives fragmentation (share of neighbours in a different class) and landscape diversity
(Shannon entropy over neighbourhood class fractions). Costs and the `k` decision: §10.2–10.3.

### E. Global climate regulation, physical ✅

Carbon stock (retention) over the EAA. `carbon` is a per-cell **total**, so `SUM` is correct here — the
opposite of the MSA rule in C, and the aggregation trap the system prompt must state explicitly. The
collection carries `h8` as a column, so no `h3_cell_to_parent` call is needed.

```sql
WITH aoi AS (
  SELECT DISTINCT h8
  FROM read_parquet('s3://public-overturemaps/2026-02-18.0/countries/hex/h0=*/data_0.parquet')
  WHERE h0 IN (578290339652042751, 578395892768309247)
    AND country = 'CR' AND class = 'land'
)
SELECT ROUND(SUM(c.carbon) / 1e6, 2) AS mt_irrecoverable_c
FROM read_parquet('s3://public-carbon/irrecoverable-carbon-2024/hex/h0=*/data_0.parquet') c
SEMI JOIN aoi a ON c.h8 = a.h8
WHERE c.h0 IN (578290339652042751, 578395892768309247);
```

Costa Rica: **52.93 Mt C** irrecoverable (2024), over 763,385 res-9 cells.

**The density-vs-amount discipline, demonstrated.** To break carbon out by ET, apportion the per-cell
*total* by `frac` and then sum — the mirror image of task C, where an *intensity* is weighted by area and
then averaged. Both layers are native res 9, so the join is exact:

```sql
SELECT f.lc_class,
       ROUND(SUM(c.carbon * f.frac) / 1e6, 2) AS mt_carbon,
       ROUND(SUM(c.carbon * f.frac)
             / (SUM(f.frac * h3_cell_area(f.h9,'km^2')) * 100), 1) AS mgC_per_ha
FROM f JOIN c ON c.h9 = f.h9 ... GROUP BY f.lc_class;
```

| ET | Mt C | Mg C/ha |
|---|---:|---:|
| 112 Closed forest, evergreen broadleaf | 36.76 | 16.1 |
| 40 Cropland | 5.06 | 3.1 |
| 126 Open forest, unknown | 3.82 | 6.1 |
| 90 Herbaceous wetland | 2.15 | **37.6** |
| 50 Urban / built-up | 0.09 | 1.4 |

Wetland carries the highest density and cropland/urban the lowest, as expected. The per-ET total is
51.4 Mt against the whole-cell 52.93 Mt; the 1.5 Mt difference is carbon sitting in the sea and water
fractions of coastal cells, correctly excluded here and correctly included above.

⚠️ Licence: irrecoverable-carbon is **CC BY-NC 4.0**, non-commercial only. See `PROVENANCE.md`.

The sequestration *flow* half of this service still needs ingest #3.
