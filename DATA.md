# Data acquisition plan

Companion to [`DESIGN.md`](DESIGN.md). This document answers: **what is best-in-class for each SEEA EA
account component, what do we already hold, what must we import, and what will the licence let us do.**

The premise is deliberate: we are *not* scoping to the existing GLEN catalog. The catalog is a starting
inventory, and several of the layers already in it are the wrong choice for accounting work.

> **Companion:** [`PROVENANCE.md`](PROVENANCE.md) classifies every layer by *evidence* — documented
> standard vs. ARIES's actual choice vs. published national practice vs. our own pick. It revises two
> recommendations in this document: ESA CCI LC has a comparability claim GLC_FCS30D does not (§1.2 there),
> and `irrecoverable-carbon` is **not** the standard carbon source — IPCC Tier 1 coefficients are (§1.1).

---

## 1. The governing framework: UNSD Tiers

There is official guidance we should conform to rather than invent around. UNSD's
**Guidelines on Biophysical Modelling for Ecosystem Accounting** (2022) — adopted as part of the SEEA EA
implementation strategy approved at the 53rd Statistical Commission — defines a three-tier scheme:

| Tier | Definition (UNSD) | What it is fit for |
|---|---|---|
| **Tier 1** | "relies on globally available data sets and pre-constructed ecosystem service models using freely available tools, requiring very little user input" | "'order of magnitude' aggregate estimates of annual flow of ES … adequate for awareness raising purposes" |
| **Tier 2** | "relies on national data sets, requiring some customization and validation" | "identify national trends in ecosystem services across periods, including disaggregation at national sectoral level" |
| **Tier 3** | "implemented based on the best available local data using customized models … parametrized for local contexts" | "trends in ES at the property boundary level … a basis for land-use planning policies or instrument design at property level" |

**This is the honest frame for our whole project.** unseea is a **Tier 1 system with a Tier 2 upgrade
path**: global defaults everywhere, with national data substitutable per-EAA as we ingest it. That is a
legitimate and UNSD-endorsed starting point — "many organizations may choose to initiate ecosystem
accounts compilation using a Tier 1 approach."

It also draws a hard boundary around the word "planning" in our own title. UNSD reserves
property-boundary land-use planning for **Tier 3**. Our scenario engine (DESIGN.md §6.3) is therefore a
**screening and awareness instrument** — "which of these options is worth a real study" — not a
parcel-level decision system. The app must say so, and the minimum-area guard (DESIGN.md §5.4) is how it
says so in practice.

Two further points from the guidance worth designing around:

- Tiers are **per-attribute, not per-account**: "A model may be in Tier 1 for some attributes, while
  having Tier 3 characteristics for others." So tier should be recorded **per service, per variable**,
  not as one global badge. It belongs in the methods record.
- **Upgrades must be retrospective**: "When a country changes the Tier of a specific account … it is
  recommended to redo compilation also for earlier years, so as to generate a consistent time series."
  This is an architectural requirement — versioned ingests and cheap recomputation of history, not
  in-place layer replacement.

### 1.1 Reference documents to obtain

| Document | Why | Status |
|---|---|---|
| SEEA EA (2021) White Cover | The standard | ✅ in [`research/`](research/) |
| **Guidelines on Biophysical Modelling for Ecosystem Accounting** (2022, 221 pp) | Recommended model + data source per service; Tier definitions; condition-indicator tables | ✅ obtained, in [`research/`](research/) |
| **Supplemental tables** to the above ([seea.un.org](https://seea.un.org/content/supplemental-materials-and-tables-guidelines-biophysical-modelling)) — Tables 4, 5, 13–18, 25, 28, maintained as living documents | Table 28 = global data sources; 13–18 = condition indicators per ECT class; 25 = platform capability matrix | **TODO — fetch current versions** |
| **Technical report on Monetary Valuation of Ecosystem Services and Assets** (interim) | The valuation half; needed for accounts 4 and 5 | **TODO** |
| **SEEA ES Reference List Crosswalk** + **Ecosystem Services Logic Chains** (published with SEEA EA) | Official crosswalk to CICES and other lists; needed to reconcile ENCORE's 21 services and EXIOBASE sectors to SEEA's ~27 | **TODO** |
| **SEEALand complementary spreadsheet** | Cell-level condition workings and NPV-by-ET sheets behind Annex Tables A.4/A.10 | **TODO — blocks Phase 1** |

---

## 2. Licence classification

Everything below is tagged with one of these. This is the axis most likely to bite us late.

| Tag | Meaning | Consequence for us |
|---|---|---|
| 🟢 **Open** | CC0 / CC BY / public domain | Ingest, republish as hex, serve tiles. No constraint. |
| 🟡 **Copyleft** | CC BY-SA | Derived layers inherit ShareAlike. Cannot be mixed into a uniformly CC BY catalog without care. |
| 🟠 **Non-commercial** | CC BY-NC | Republishing is permitted; *commercial* use by our users is not. Needs a per-layer notice. |
| 🔴 **No redistribution** | Bespoke restrictive terms | **We may not republish it at all.** Requires written permission or an architectural workaround. |

### 2.1 Restrictive licences are already inventoried — build on that, don't redo it

**Correction to an earlier draft of this document:** I initially flagged the WDPA redistribution terms as
an unnoticed compliance gap. That was wrong. `data-workflows` already maintains
[`catalog/sync/source-coop/license-inventory.md`](https://github.com/boettiger-lab/data-workflows/blob/main/catalog/sync/source-coop/license-inventory.md)
— a full recursive STAC walk (130 nodes) with a per-collection verdict:

> **OK** mirror freely · **OK-NC** mirror with NC/SA label · **NO** redistribution prohibited (NRP-only) ·
> **HOLD** confirm with upstream before mirroring · **N/A** meta/catalog node

Current tally: **112 OK · 16 HOLD · 10 NO · 8 OK-NC.** The relevant verdicts are already recorded and
marked *verified*:

| Collection | Verdict | Recorded reason |
|---|---|---|
| `public-wdpa`, `.../wdpa`, `.../wdoecm-may-2026` | 🔴 **NO** · `UNEP-WCMC custom` | "Protected Planet: no redistribution incl. derivatives (verified)" |
| `public-iucn`, `.../iucn-ranges-2025`, `.../taxonomy` | 🔴 **NO** · `IUCN Red List ToU` | "IUCN: no redistribution, incl. derivatives (verified)" |
| `public-icca` (+ point/polygon) | 🔴 **NO** · `UNEP-WCMC custom` | Protected Planet terms (verified) |
| `public-hydrobasins` | 🔴 **NO** · `HydroSHEDS v1 custom` | "no stand-alone redistribution … v1c not CC-BY" — replacement tracked in **#223** |
| `public-gfw`, `public-carbon` | 🟠 **OK-NC** · `CC-BY-NC-4.0` | mirror with NC label |
| `public-land-cover/{cgls-lc100-2019, nlcd-2024}` | 🟢 **OK** | CC-BY-4.0 / US federal PD |
| `public-globio`, `public-population/ghs-pop-2020`, `public-overturemaps` | 🟢 **OK** | CC-BY-4.0 / CDLA-Permissive-2.0 |

Epic **#449** also codifies the policy: source.coop is public open-data infrastructure, so **NC and SA
are mirror-eligible** (propagate the clause, label the licence); only **No-Derivatives** and **custom
no-redistribution / request-access** terms are ineligible. Mechanically this is a two-tier distribution
model — NRP + MinIO as primary, source.coop as the public mirror — with per-*dataset* `EXCLUDES` so one
restricted collection doesn't disqualify its whole bucket. There is prior art for licence-gated imports
(**#461** ParkServe, "license clearance required") and for NC-restricted scientific reproduction
(**#430**, IUCN STAR).

**So what remains genuinely open for unseea:**

1. **The inventory's verdict is scoped to *mirroring*, not to primary access.** The NRP buckets are
   anonymously readable and reachable through a public MCP endpoint and public web maps. Whether that
   primary copy is itself "redistribution … through web services" under the Protected Planet terms is a
   narrower question than source.coop eligibility, and unseea would lean on it harder than most apps —
   protected areas are an EAA type, a condition covariate, and the basis of SEEA Ch. 13 thematic
   protected-area accounts. Worth an explicit confirmation from whoever owns the call.
2. **Permission would change the verdict, not just our comfort.** Written UNEP-WCMC permission would move
   WDPA/OECM/ICCA from **NO** to mirror-eligible and remove the constraint for downstream users.
3. **The contact is still worth making, for wider reasons** — ENCORE bulk data and licence terms (§6.2),
   plus ARIES comparison access (DESIGN.md Phase 4). UNEP-WCMC is the custodian of WDPA, a partner in
   ENCORE, and a co-developer of ARIES for SEEA: **one conversation plausibly unblocks all three.**

Interim substitutes: `pad-us-4.1` (public domain) and `cpad-2025b` for US work — which is all DESIGN.md
Phases 1–2 need. Note the **IUCN GET maps are separately CC BY 4.0** and carry none of the Red List
restrictions; do not conflate them.

---

## 3. Ecosystem extent (account 1)

The reference classification is IUCN GET; the observation layer must be wall-to-wall and multi-temporal.
See DESIGN.md §5.1 for why these are two different jobs.

| Need | Best-in-class | Res / coverage / time | Licence | Status |
|---|---|---|---|---|
| **ET classification, wall-to-wall** | **World Terrestrial Ecosystems 2020** (USGS/Esri/TNC, Sayre et al.) — ScienceBase [10.5066/P9DO61LP](https://www.sciencebase.gov/catalog/item/6296791ed34ec53d276bb293) | 250 m, global terrestrial, **431 classes**, 2020 static | 🟢 public-domain (USGS) / CC BY 4.0 (Living Atlas) | **queued #438** |
| ET reference classification (labels) | **IUCN GET Level 3 (EFG) v2.1** — [Zenodo 10081251](https://zenodo.org/records/10081251) | ecoregion-template, ~110 indicative EFGs, static | 🟢 CC BY 4.0 | **queued #438** (stretch goal) |
| Global extent + **change** | **GLC_FCS30D** — [ESSD 16:1353](https://essd.copernicus.org/articles/16/1353/2024/) | 30 m, global, 1985–2022 (5-yearly to 2000, then **annual**), 35 classes | 🟢 CC BY 4.0 (Zenodo) | ❗ **net-new — top priority** |
| Cross-check / alternate | ESA WorldCover 10 m (2020/2021) **#439**; ESA CCI LC (300 m, 1992–2022, annual); Dynamic World (10 m, 2015–) | | 🟢 | #439 queued |
| Current global snapshot | `cgls-lc100-2019` **hex-fractions** | 100 m→h3 res 9, 2019 only | 🟢 OK | ✅ have |
| CONUS extent + change | **NLCD Annual + Land Cover Change** | 30 m→h3 res 10, **1985–2024**, hex-fractions-first | 🟢 public domain | **queued #453 (scope-locked 2026-07-27)** |
| Mangroves | **Global Mangrove Watch** (1996–2020) | 25 m | 🟢 CC BY | **queued #443** |
| Coral reefs | **Allen Coral Atlas** | 10 m | 🟢 CC BY | **queued #444** |
| Seagrass | UNEP-WCMC global seagrass | polygon | 🔴 WCMC terms (#449 marks ineligible) | **queued #444** — NRP-only |
| Surface water (F1/F2) | **JRC Global Surface Water** (Pekel) | 30 m, 1984– | 🟢 | **queued #441** |
| Wetlands (TF1) | `wetlands-glwd-v2`, Ramsar | | 🟢 / mixed | ✅ have |
| Marine/subterranean ETs | `meow-ecoregions`, `seafloor-geomorphology`, `gebco-2025` | | 🟢 | ✅ have |
| EAA boundaries | `overture-divisions-*` (🟢 CDLA-Permissive), `usgs-wbd`; HydroSHEDS/HydroBASINS **#442/#223**; **FAO GAUL / UN M49** for official reporting units | | mixed | ✅ partly — M49 net-new |

### 3.1 WTE resolves the GET overlap problem better than a crosswalk

This is the most important thing the issue tracker changed about the design. DESIGN.md §5.1 originally
proposed resolving IUCN GET's overlapping indicative maps against land cover via a hand-curated
crosswalk. **World Terrestrial Ecosystems (#438) is a better answer**, for three reasons:

1. It is **wall-to-wall and mutually exclusive** — so ET areas sum to the EAA, which is the extent
   account's own internal check. GET's indicative maps cannot do this; #438 says so in as many words
   ("ecoregion-derived indicative distributions, not a fine wall-to-wall grid").
2. **SEEA EA names it explicitly.** §3.67 lists "classes present in the World Terrestrial Ecosystems for
   terrestrial areas (Sayre et al., 2020)" among the classifications correspondences will be developed
   for. Using it is conformant, not a deviation.
3. Its **431 classes decompose as landcover × climate × landform**, which is a far richer basis for a
   GET crosswalk than a 23-class land-cover legend — and the climate/landform factors are exactly what
   distinguishes GET EFGs within a biome.

Revised division of labour: **WTE = the ET partition** (static, wall-to-wall, sums correctly) ·
**GET = the reference-classification label** attached to WTE classes via crosswalk · **land-cover time
series = the change detector** driving additions and reductions. GET's major/minor occurrence becomes a
*validation* signal on the crosswalk rather than a load-bearing input.

The caveat: **WTE is a single 2020 epoch**, so it cannot supply change on its own. The extent account
therefore needs both WTE (what type) and a land-cover time series (what changed) — which is why
GLC_FCS30D remains the top net-new ask.

Prior art for the crosswalk itself already exists: **#427** imports the IUCN habitat ↔ land-cover
crosswalk (Lumbierres 2021, against CGLS-LC100) as an AOH/STAR prerequisite. Same shape of artefact, same
review burden — worth following its pattern rather than inventing one.

### 3.2 One build-convention ask: fractions, not mode, for extent-critical layers

Epic #449's standard conventions set global categorical rasters to **native H3 res 8, reducer `mode`**.
For map styling that is right. For **extent accounting it is not**: `mode` assigns one class per cell and
discards the within-cell mix, and at res 8 (~0.74 km²) that materially distorts per-class area in any
heterogeneous landscape — which is most of them. Areas would not reconcile, and the extent account's
balance check would fail for reasons unrelated to the data.

The fractional pattern is already established in the catalog (**#301** reprocessed categorical mode hexes
with fractional coverage; `cgls-lc100-2019` and `nlcd-2024` both ship `hex-fractions`), and **#453 is
already scope-locked to "hex-fractions-first"** for NLCD Annual. The ask is to extend that to the global
extent-critical layers — **WTE (#438), WorldCover (#439)**, and any land-cover time series — as an
additional `hex-fractions` asset alongside `mode`.

Also worth noting for DESIGN.md §2.2: at the #449 convention of native res 8, our **BSU is ~0.74 km²**,
not the ~0.106 km² of res 9. That tightens the minimum-area guard (DESIGN.md §5.4) — a defensible global
EAA floor is nearer 50–100 km² than 10 km². CONUS work on NLCD res 10 (~0.015 km²) is much finer.

Note UNSD's own framing in supplemental Table 5 — "key properties of freely available global land cover
products … One feature that is important for SEEA EA, especially for land cover data, is **coverage over
multiple years**." Our current global holding fails precisely that test; #453 fixes it for CONUS only.

---

## 4. Ecosystem condition (account 2)

Organised by ECT class. UNSD supplemental Tables 13–18 are the authoritative shortlist per class and
should be fetched before finalising; below is best-in-class as currently identifiable.

| ECT class | Best-in-class | Licence | Status |
|---|---|---|---|
| **A1 Physical** | **SoilGrids 2.0** (250 m: bulk density, texture, coarse fragments); Global High-Resolution Soil-Water Balance (1 km, AET / soil water stress); `copernicus-glo90` DEM for slope | 🟢 CC BY 4.0 | **#446** (SOC-scoped — ask to widen); DEM ✅ |
| **A2 Chemical** | **SoilGrids 2.0** SOC + pH + CEC + N; global soil salinity (250 m, 7 epochs); air quality — **Van Donkelaar PM2.5** (1 km, 1998–, SEDAC); water quality — GEMStat (station, sparse) | 🟢 mostly | **#446** partial; PM2.5 ❗ net-new |
| **B1 Compositional** | `globio-msa-2015-overall` (+ plants / wb-vert; **has 2050 SSP1/3/5 scenarios**); **BII** (PREDICTS); `iucn-richness-2025`; **GBIF** via `gbif-derived` | 🟢 GLOBIO (#463 done); 🟠 BII CC-BY-NC-SA; 🔴 IUCN spatial | ✅ GLOBIO have; **BII queued #435** |
| **B2 Structural** | **Hansen Global Forest Change v1.13** (30 m, 2000–2025: treecover2000, lossyear, gain); **ESA CCI Biomass + Spawn & Gibbs** (AGB); **ETH canopy height 10 m**; `rap-*` CONUS | 🟢 CC BY 4.0 | **queued #434/#209, #445, #440** |
| **B3 Functional** | **Copernicus Global Land Dry Matter Productivity** (300 m, 10-daily, 2014–) or **MODIS MOD17 NPP** (500 m, annual, 2000–); LAI from Copernicus | 🟢 | ❗ **net-new — class currently empty** |
| **C1 Landscape** | **computed from our own hex extent layer** — see DESIGN.md §4.4. `global-human-modification` (#210) and **FLII annual** (#470) as pressure-side covariates | 🟢 | derive; #210/#470 queued |

Two notes:

- **GLOBIO MSA is the anchor variable** for B1 and should stay so: it is already normalised [0,1]
  against an undisturbed reference, which means the variable→indicator step needs no reference-level
  lookup, and its SSP scenario layers give a ready-made condition trajectory for scenario work.
- **B3 functional is our thinnest class and the cheapest to fix.** One NPP/DMP ingest lights up an
  entire ECT class across every ET. High value per unit effort.

For reference levels (DESIGN.md §5.3), UNSD §5.7 covers modelling approaches; the tractable global
options remain ecoregion-percentile ambient distributions and prescribed levels. `wwf-ecoregions-2017`
and `meow-ecoregions` are the stratification, and we hold both.

---

## 5. Ecosystem services (accounts 3 and 4)

UNSD Chapter 6 gives detailed modelling recommendations for exactly **ten** services — and these are the
ten we should target, because conformance and reviewability are worth more than breadth:

1. Crop provisioning · 2. Wood provisioning · 3. Air filtration · 4. Soil erosion control / sediment
retention · 5. Water supply · 6. Water purification · 7. Water flow regulation · 8. Global climate
regulation · 9. Pollination · 10. Recreation-related

That is a superset of ARIES's four (crop, pollination, climate regulation, erosion control) and a
credible target. DESIGN.md open question #5 is hereby answered: **ten, per UNSD Chapter 6.**

| Service | Recommended approach | Data to import | Licence / status |
|---|---|---|---|
| **Crop provisioning** | SPAM production × FAOSTAT year adjustment, then **ecosystem contribution via Vallecillo et al. (2019)** — ratio of natural to natural+human inputs in energetic terms. *This is exactly the method ARIES uses.* | **SPAM 2020** (10 km, 46 crops); **FAOSTAT** production + producer prices; FAO **GAEZ v4** Theme 4 (53 crops) | 🟢 CC BY 4.0 · ❗ **net-new** |
| **Wood provisioning** | Forest harvest from FAO FRA / FAOSTAT-Forestry, spatially allocated by observed forest loss | **Hansen GFC lossyear** (#434/#209); ESA CCI Biomass (#445); FAO FRA | 🟢 · partly queued |
| **Air filtration** | Deposition velocity × pollutant concentration × vegetation cover (i-Tree / ESTIMAP logic) | **Van Donkelaar PM2.5**; LAI | 🟢 · ❗ **net-new** |
| **Soil erosion control** | RUSLE-family: retention = potential − actual soil loss. **GloSEM** (Borrelli et al.) is the global reference | **GloSEM** (250 m, 2001/2012); rainfall erosivity **GloREDa**; SoilGrids K-factor (#446); DEM ✅ | verify GloSEM · ❗ **net-new** |
| **Water supply** | Water yield (Budyko / InVEST annual water yield) reconciled to basin runoff | **WaterGAP** or **PCR-GLOBWB** runoff; CHELSA precip (#448 — note WorldClim is 🔴 no-redistribution, CHELSA is not); **Global Runoff Data Centre** for calibration | #448 queued; runoff ❗ net-new |
| **Water purification** | N/P retention — InVEST NDR for terrestrial retention; distinguish from in-stream denitrification | N/P loading (**Global NEWS**); fertiliser (**Lu & Tian**); SoilGrids (#446); DEM ✅; HydroSHEDS (#442) | ❗ **net-new** (loading) |
| **Water flow regulation** | Baseflow index and peak-flow attenuation over HydroSHEDS/HydroBASINS | **HydroSHEDS** (#442 — 🔴 NRP-only; v2 replacement #223); **Aqueduct 4.0** (#433); soil hydraulics (**HiHydroSoil**) | #433/#442 queued |
| **Global climate regulation** | **Two components — do not conflate.** *Retention* = carbon stock; *removal* = annual sequestration flux | stock: `irrecoverable-carbon` ✅ (🟠 NC), **ESA CCI Biomass + Spawn & Gibbs** (#445), **SoilGrids SOC** (#446); flux: **GFW/Harris forest carbon fluxes** (30 m, 2001–2023) | stock queued; **flux ❗ net-new** |
| **Pollination** | Lonsdorf/InVEST pollinator abundance from land cover × nesting/floral tables, × crop pollination dependency | **Klein et al.** dependency ratios; SPAM 2020; our hex land cover | ❗ **net-new** (tables) |
| **Recreation** | Visitation models; nature-access population overlay | **Chaplin-Kramer et al. 2022 critical natural assets / NCP layers** (nature access, coastal risk reduction, sediment & N retention); `ghs-pop-2020` ✅; `parkserve`/`federal-trails` US ✅ | verify NCP terms · ❗ **net-new** |

Beyond the ten, cheap wins we already hold or nearly hold: **grazed biomass** (`nci-frontiers` grazing +
**GLW 4** livestock density, 🟢 CC BY 4.0), **coastal protection** (mangroves + coral + `gebco-2025` +
population), **wild fish** (see §5.1), **nursery/habitat maintenance** (`kba`, `imma`, `ebsa` — intermediate
service, do not add to the aggregate).

### 5.1 Marine services are a licence trap

The obvious marine provisioning sources are both 🟠 non-commercial: **Global Fishing Watch** (CC BY-NC
4.0 — already in our catalog as `gfw-fishing-effort`) and **Sea Around Us** catch reconstructions (CC
BY-NC 4.0). Neither blocks a research deployment, but both must carry an NC notice, and neither can
support a commercially-used product. Since marine is open ground relative to ARIES (terrestrial-only),
decide the commercial posture *before* investing in the marine vertical.

### 5.2 A note on model porting

UNSD's recommendations lean on InVEST, ARIES, ESTIMAP, i-Tree and LUCI/Nature Braid (supplemental
Tables 4 and 25). We are not going to run InVEST. For each of the ten, the question is whether the model
reduces to **per-cell algebra plus neighbourhood or flow-routing operations** — because that is what
DuckDB over h3 does well:

- **Reduces cleanly** (per-cell algebra or k-ring): crop, wood, air filtration, pollination, climate
  regulation, recreation. These are honest Tier 1 reimplementations.
- **Needs flow routing** (upstream/downstream accumulation): erosion/sediment delivery, water
  purification, water flow regulation. H3 is not a flow-routing grid. Two options: precompute the
  routed result offline per basin and ingest it as a layer, or ingest a published global model output
  (GloSEM, Global NEWS) and treat it as the observation. **Prefer ingesting published outputs** — it
  is more defensible than a hand-rolled routing approximation, and it is what Tier 1 means.

That split should drive the ingest list: the routing-dependent services are *layer imports*, not
in-app models.

---

## 6. Monetary accounts (accounts 4 and 5) — and where ENCORE and EXIOBASE fit

This is the part with no remote-sensing answer, and where your instinct about ENCORE and EXIOBASE is
right.

### 6.1 EXIOBASE — the residual-value engine and the use table

**EXIOBASE 3** is a global multi-regional environmentally-extended supply-use and input-output table:
**163 industries × 200 products × 49 regions** (44 countries + 5 rest-of-world), annual 1995 onward,
with satellite accounts for land use, water, materials and GHG. Hosted on
[Zenodo](https://zenodo.org/records/15689391). Licence 🟡 **CC BY-SA 4.0**.

Three distinct jobs it does for us, in descending order of importance:

1. **It solves the ecosystem-contribution problem.** DESIGN.md §5.2 flagged the sharpest risk in the
   monetary accounts: `nci-frontiers` gives crop *revenue*, but SEEA wants the ecosystem's
   *contribution*, and booking revenue directly overstates the account by whatever share belongs to
   labour and capital. A residual-value / resource-rent calculation needs gross value added and
   intermediate input structure by industry and region — which is precisely EXIOBASE's content. This
   turns a hand-waved coefficient into a documented derivation.
2. **It populates the use table.** SEEA Ch. 7 use tables allocate service use across industries,
   households, government, accumulation and exports. EXIOBASE's industry classification is the natural
   spine, and its final-demand structure gives the household/government split.
3. **It makes imports and exports of ecosystem services tractable.** Ch. 7.2.6 requires these, and they
   are otherwise nearly unanswerable — a country's crop provisioning use is not its production. MRIO is
   the standard instrument for exactly this telecoupling question, and nothing else gets us there.

**The 🟡 copyleft caveat is real.** CC BY-SA means derived works inherit ShareAlike, which conflicts with
publishing a uniformly CC BY hex catalog. Workaround: keep EXIOBASE-derived material as a **separately
licensed module** — coefficient tables, clearly marked CC BY-SA, not blended into other layers. Since
what we need are national/sectoral *coefficients* rather than a spatial grid, this is easy to isolate:
they are lookup tables joined at query time, not a hexed layer. Do not let EXIOBASE coefficients leak
into a published hex layer.

### 6.2 ENCORE — a qualitative prior, not a quantitative input

**ENCORE** covers **167 economic sectors × 21 ecosystem services**, rating dependencies (and, in later
versions, impacts) on natural capital. Now maintained by the **ENCORE Partnership — Global Canopy, UNEP
FI and UNEP-WCMC** — at [encorenature.org](https://encorenature.org), free and described as open-access,
with a 2024 data update.

Be clear about what it is: the dependency ratings are **ordinal** (materiality categories), not
quantitative coefficients. So ENCORE's role is:

- ✅ a defensible prior for **which** industries plausibly depend on **which** services — i.e. which
  cells of the use table should be non-zero, and which are structurally empty;
- ✅ a sanity check on our own allocations, and a bridge to the nature-related financial disclosure
  audience (TNFD), which is a real user constituency for a SEEA tool;
- ❌ **not** a source of magnitudes. Do not multiply by an ENCORE rating.

Two open items: no documented **API or bulk download** was found, and the underlying **data licence is
not stated** on the about page — only terms-and-conditions and a data-security statement are linked.
Both need resolving by contact. Fold this into the §2.1 UNEP-WCMC request, since WCMC is a partner in
ENCORE, the custodian of WDPA, and a co-developer of ARIES for SEEA. **One conversation plausibly
unblocks WDPA redistribution, ENCORE bulk data, and ARIES comparison access.** That is the single
highest-leverage non-technical action in this plan.

Also required: a crosswalk from ENCORE's 21 services to SEEA's ~27, which is what the official
**ES Reference List Crosswalk** supplement (§1.1) exists for. Do not improvise it.

### 6.3 Prices and value transfer

| Need | Source | Licence |
|---|---|---|
| Crop, livestock, forestry producer prices | **FAOSTAT** producer prices | 🟢 CC BY 4.0 |
| Commodity prices | **World Bank "Pink Sheet"** | 🟢 |
| Carbon price | **World Bank Carbon Pricing Dashboard** (ETS/tax prices) — and, separately and clearly labelled, SCC estimates | 🟢 |
| Timber / roundwood | **FAOSTAT-Forestry** | 🟢 CC BY 4.0 |
| Water tariffs | IBNET / national regulators | mixed |
| **Value transfer for services with no market price** | **ESVD** — 9 500+ standardised value records from 1 100+ studies, "largest open-access database with standardized monetary values for all ecosystem services and all ecosystems globally"; free with an account | verify redistribution terms |
| Value-added / intermediate inputs for resource rent | **EXIOBASE 3** (§6.1) | 🟡 CC BY-SA |

**ESVD needs care.** SEEA Ch. 9.5 explicitly addresses "spatial variation in values and value transfer,"
so value transfer is sanctioned — but most ESVD records are *welfare* values (willingness-to-pay,
consumer surplus), and SEEA Ch. 8 requires **exchange** values in the core accounts. Welfare estimates
belong in the Ch. 12 bridge table, not accounts 4 and 5. So: use ESVD to filter for exchange-value-
compatible records and for the Ch. 12 complementary presentation, and never as a default price for the
core accounts. Getting this wrong is the fastest route to a headline number a national statistician
will reject.

---

## 7. Priority sequence

**The headline: most of what unseea needs is already queued.** Epic **#449** (TNFD/SBTN global gaps) plus
**#453** covers roughly two-thirds of this plan, and its LEAP/SBTN framing maps almost cell-for-cell onto
SEEA's accounts — *Locate* ≈ extent, *Assess* ≈ condition, *Evaluate* ≈ services. That is a fortunate
overlap and the plan should exploit it rather than duplicate it.

### 7.1 Align with what exists (no new issues needed)

| unseea need | Already tracked |
|---|---|
| ET classification, wall-to-wall + GET labels | **#438** (WTE 250 m + GET stretch) |
| CONUS extent + **change** | **#453** (scope-locked, 1985–2024, hex-fractions-first) |
| Condition B2 structural | **#434**/**#209** Hansen GFC · **#445** biomass · **#440** canopy height |
| Condition B1 compositional | **#463** GLOBIO ✅ done · **#435** BII |
| Condition A1/A2 | **#446** SoilGrids 2.0 |
| Condition C1 pressure covariates | **#210** gHM · **#470** FLII annual |
| Water flow regulation / water risk | **#433** Aqueduct 4.0 · **#442** HydroSHEDS · **#223** HydroBASINS v2 |
| Grazed biomass | **#447** GLW 4 |
| Marine / transitional extent | **#443** mangroves · **#444** coral & seagrass · **#441** surface water |
| Bioclimate inputs | **#448** CHELSA + Köppen |
| Crosswalk pattern precedent | **#427** IUCN habitat ↔ land-cover (Lumbierres 2021) |
| Provenance / audit trail | **#417** upstream URL + access date + checksum at ingest |

**Two comments to file on existing issues** rather than new work:

- **#438** — request the **`hex-fractions` asset** in addition to `mode`, and promote GET from stretch
  goal to in-scope (it is the SEEA reference classification, and 🟢 CC BY). §3.1–3.2.
- **#439** — same fractions request for WorldCover. §3.2.

### 7.2 Net-new asks, in order of unblocking power

**P0 — two are conversations, not code.**

1. **Fetch the outstanding reference documents** (§1.1) — the **SEEALand complementary spreadsheet blocks
   DESIGN.md Phase 1**, and the UNSD supplemental Tables 13–18/25/28 should shape §4 before we build it.
   Zero dependencies; do it now.
2. **Contact UNEP-WCMC** — ENCORE bulk data + licence terms, ARIES comparison access, and possible WDPA
   permission that would move it from **NO** to mirror-eligible (§2.1, §6.2). Non-technical, high leverage.
3. **GLC_FCS30D** as annual `hex-fractions` — ❗ **the single biggest technical unblock, and not on the
   list.** #439 (WorldCover) is two epochs and #453 is CONUS-only, so nothing currently queued gives
   global extent *change*. Four of five accounts depend on it outside CONUS. **File this issue.**

**P1 — each fills a whole account row that nothing queued covers.**

4. **NPP / DMP** — the entire B3 functional condition class is empty and one ingest fills it (§4).
5. **GFW/Harris forest carbon flux** — #445 gives carbon *stock*; the annual *removal* flux half of
   global climate regulation is missing (§5).
6. **SPAM 2020 + FAOSTAT** — turns crop provisioning from a revenue proxy into a real service with the
   Vallecillo ecosystem-contribution step (§5).
7. **Van Donkelaar PM2.5** — carries both air filtration (service) and A2 chemical condition (§4, §5).

**P2 — the economic spine, and wholly absent from the tracker.**

8. **EXIOBASE 3** coefficient extraction — resource rent, use tables, service imports/exports (§6.1).
   Keep 🟡 licence-isolated as lookup tables, never blended into a hex layer.
9. **ESVD** extraction, exchange-value-filtered (§6.3).
10. **ENCORE** crosswalk to the SEEA reference list (§6.2), gated on P0-2.

These three are a different *kind* of ingest — non-spatial, national/sectoral lookup tables rather than
hexed rasters — so they may not belong in `data-workflows` at all. Worth deciding where they live before
filing.

**P3 — routed-model outputs and marine.**

11. **GloSEM**, **Global NEWS**, **WaterGAP/PCR-GLOBWB**, **HiHydroSoil** — the flow-routing services we
    should import rather than model (§5.2).
12. **Chaplin-Kramer NCP layers** — recreation/nature access, coastal risk reduction (§5).
13. **UN M49 / FAO GAUL** official reporting boundaries — needed for statistical-office-comparable EAAs.

Note that DESIGN.md Phases 1–2 need **no new global ingest at all** — #453 alone makes Phase 2
shippable. That was deliberate: correctness work proceeds in parallel with data acquisition, not behind it.

---

## 8. Decisions needed

1. **Commercial posture.** Several strong sources are 🟠 NC (GFW, Sea Around Us) or 🔴 restricted (WDPA,
   IUCN spatial). If unseea must permit commercial use downstream, the marine vertical and the
   protected-area accounts both need rethinking. If it is research/UN-facing, the §2.1 request resolves
   nearly everything. **This decision gates §5.1 and §7 P3.**
2. **Does the app surface licence, or only the catalog?** Catalog-side hygiene is already solved —
   `license-inventory.md`, SPDX `license` in STAC, `verify-stac.py` gating, and #103 closed. The open
   question is unseea-side: should the account output carry per-layer licence and attribution into the
   methods record and the XLSX export? For a tool aimed at statistical offices, probably yes — and it
   composes neatly with **#417** (upstream URL + access date + checksum at ingest), which would give the
   audit trail a verifiable provenance chain rather than a hand-written citation list.
3. **Ten services, or fewer done better?** §5 commits to UNSD's ten. Given P1 alone covers crop, wood,
   climate regulation and pollination, a defensible v1 might be those four plus erosion control — matching
   ARIES's coverage exactly, which makes head-to-head validation clean, and adding breadth afterwards.
4. **Who owns the ingests, and where do the non-spatial ones live?** The raster asks are
   `data-workflows` issues, and GLC_FCS30D (30 m, global, annual, 35 classes, long-format fractions) is a
   genuinely large job — larger than anything in #449. The EXIOBASE/ESVD/ENCORE tables are a different
   artefact class and may belong elsewhere (§7.2 P2). Sequencing depends on that capacity, not on this
   document.
