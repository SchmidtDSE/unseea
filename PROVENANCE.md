# Layer provenance: standard choice, or our best guess?

For every layer this app uses, this document answers one question: **is this what SEEA analyses actually
use, or is it our own conceptual pick?** Each entry carries an evidence class and a citation you can check.

Companion to [`DATA.md`](DATA.md) (what to acquire) and [`DESIGN.md`](DESIGN.md) (why).

## Why this matters

Two of our differentiators — *replication and validation* against published accounts, and *agreeing with
ARIES where both can compute the same account* — only work if we know where we've deviated. A layer that
is better in the abstract but different from what everyone else used will produce a divergence we cannot
attribute. Conceptual quality and comparability are **different axes**, and for a statistical standard
comparability often wins.

## Evidence classes

| Class | Meaning |
|---|---|
**①** | **Named in SEEA EA or the UNSD Guidelines on Biophysical Modelling** as a recommended source, model or reference classification. The closest thing to a standard that exists. |
**②** | **Used by ARIES for SEEA** — the reference implementation's actual choice. |
**③** | **Used in a published national/regional SEEA compilation** (UNSD Guidelines Tables 10, 23, 27). Documented practice. |
**B** | **Best-available — our pick.** Either no standard exists, or the standard is unusable/superseded at global scale. Must be justified and flagged in the methods record. |
**N** | **No standard exists** for this step at all. Every compiler improvises. |

A layer can hold several classes. **①②③ together is as strong as this domain gets.**

Primary sources, both in [`research/`](research/):
- **SEEA EA (2021)** White Cover, 393 pp
- **UNSD Guidelines on Biophysical Modelling for Ecosystem Accounting (2022)**, 221 pp — Table 5 (land cover products), Table 10 (country extent practice), Tables 13–18 (condition indicators per ECT class), Table 23 (country condition practice), Table 25 (ES platform capability), Table 26 (Klein pollination dependence), Table 27 (country ES practice), Table 28 (major data sources), and §6.4.1–6.4.10 "Data sources and Tiers" per service.

---

## 1. Headline findings

Three things the evidence changed.

### 1.1 ⚠️ Our carbon layer is not the standard one

**`irrecoverable-carbon` is class B, not ①.** The documented standard for global climate regulation is the
**IPCC Tier 1 stock-difference method with IPCC default coefficients**, and specifically —
UNSD §6.4.8.3 ¶314, describing ARIES for SEEA:

> "ARIES for SEEA has implemented an IPCC Tier 1 approach following specifications of **Ruesch and Gibbs
> (2008)**. It measures vegetation carbon and soil carbon separately. For vegetation carbon it is based on
> a multi-layer look-up table with IPCC coefficients that stratify according to 5 data layers, namely:
> **land cover, ecofloristic region, continent, presence of frontier forests** (proxy for forest
> degradation), **recent occurrence of fires**. Soil carbon storage data rely on spatial data, e.g., from
> **ISRIC** [SoilGrids]."

Irrecoverable carbon (Noon et al. 2022) is a *conservation-prioritisation* construct — carbon that is
manageable and unrecoverable within 30 years. That framing is deliberately **not** a total accounting
stock, so it cannot fill the SEEA global climate regulation row without a caveat. It is excellent for
targeting; it is the wrong quantity for an account.

**Recommendation:** implement the **IPCC Tier 1 lookup** as the primary path — land cover × ecofloristic
region × continent × IPCC coefficients, with soil carbon from SoilGrids. This is a *lookup table joined to
our hex land cover*, which is cheap and exactly the shape h3 + DuckDB is good at. Keep
`irrecoverable-carbon` as a secondary/thematic layer.

Note also the standard's own admitted weakness (¶315): in both InVEST and ARIES "changes in storage are
**predominantly driven by land cover change (not by ecosystem degradation)**." Our design attributes
degradation to *condition* change, so we can improve on this — but that is a deliberate deviation to
declare, not a silent upgrade.

### 1.2 ⚠️ ESA CCI Land Cover has a comparability claim GLC_FCS30D does not

I previously recommended **GLC_FCS30D** as the top ingest on quality grounds. That still holds on quality
— but UNSD Table 5's shortlist of global land cover products (CCI, MODIS MCD12Q1, Copernicus, GlobeLand,
FROM-GLC) singles out one for multi-year work, and the text is explicit (¶131):

> "…the best available time series of land cover data products (**CCI LC 300m**)."

**ESA CCI LC** is the only annual, decades-long product in that table (1992–2019 as published; now
1992–2022+ via Copernicus C3S), and it is what much of the documented national practice used. So:

| | ESA CCI LC 300 m | GLC_FCS30D 30 m |
|---|---|---|
| Evidence | **①③** — named by UNSD, used in practice | **B** — newer, not yet in any guidance |
| Resolution | 300 m | 30 m |
| Temporal | annual 1992–2022+ | 5-yearly 1985–2000, annual 2000–2022 |
| Value to us | **comparability** with published accounts | **accuracy**, esp. fragmented landscapes |

**Recommendation: ingest both**, and make CCI LC the conformance baseline for replication work (Phase 4)
while GLC_FCS30D carries the fine-grained scenario and small-EAA work. If only one, CCI LC is the safer
first move — it is also cheaper (300 m vs 30 m, global, annual). This is a revision to
[`DATA.md`](DATA.md) §7.2 P0-3 and boettiger-lab/data-workflows#498.

### 1.3 Ecosystem condition has essentially no global standard

UNSD Table 23's documented condition accounts are **national data and bespoke indices** without
exception — Norway's Nature Index (monitoring + expert judgment), South Africa's river Condition Index
(expert review), Peru's Generalised Dissimilarity Modelling via BILBI, Mexico's Ecosystem Integrity Index
(Bayesian network). Nothing global, nothing reusable.

So most of our condition account is honestly class **B/N**, and we should say so. The exceptions —
genuinely ① — are worth knowing, because they are exactly the layers already in or queued for the catalog:

- **GLOBIO MSA** — named in UNSD Table 15 by name and mechanism ✅ *have*
- **Biodiversity Intactness Index / PREDICTS** — named in Table 15 (#435)
- **ISRIC SoilGrids** — named in Table 13 (soil organic carbon) and Table 28 (#446)
- **MODIS NPP (MOD17) / Copernicus DMP / Copernicus LAI** — named in Table 17, with direct links (#499)
- **SEDAC PM2.5 grids** (van Donkelaar) — named in Table 14
- **HydroSHEDS, JRC Global Surface Water** — named in Tables 13 and 28 (#442, #441)

That is a pleasant result: the condition imports I proposed on conceptual grounds turn out to be the
named ones. **B3 functional** in particular — the empty class — is filled by precisely the datasets Table
17 lists.

---

## 2. By account

### 2.1 Ecosystem extent

| Layer | Class | Evidence |
|---|---|---|
| **IUCN GET** (Level 3 EFG) | **①②** | SEEA EA Table 3.2 adopts GET as the **SEEA Ecosystem Type reference classification**; Table 4.1 compiles at "Level 3 – EFG". ARIES uses GET for its extent accounts. |
| **World Terrestrial Ecosystems** (Sayre) | **①** *(weak)* | SEEA EA §3.67 names it among classifications for which "correspondences… will be developed" — endorsed as a crosswalk target, **not** as the reference classification. Our use of it as the wall-to-wall partition is a defensible engineering choice, not a mandate. |
| **ESA CCI LC 300 m** | **①③** | UNSD Table 5; "best available time series" (¶131). |
| **GLC_FCS30D 30 m** | **B** | Post-dates the guidance. Better; non-standard. |
| **Copernicus CGLS-LC100 100 m** | **①** | UNSD Table 5. Single year in our catalog, so snapshot-only. |
| **MODIS MCD12Q1, GlobeLand30, FROM-GLC** | **①** | UNSD Table 5 — alternatives, not our pick. |
| **Hansen Global Forest Change** | **①** | UNSD Table 6 + §4.4.3 ¶131 for forest extent change (#434). |
| **JRC Global Surface Water** | **①** | UNSD §4.4.3 ¶131 ("Surface Water Explorer"), Table 13 (#441). |
| **Global Mangrove Watch, Allen Coral Atlas** | **B** | Not named. Conceptually best-available for MFT1/M1 ETs (#443, #444). |
| **FAO LCCS classification** | **③** | Uganda and others used it (Table 10). |

⚠️ **Nobody in Table 10 used IUCN GET.** Documented country practice used FAO LCCS (Uganda), Holdridge
life zones (Guatemala), and national forest maps. GET is the standard *by the standard's own designation*
and by ARIES's implementation — but it is not yet what national compilers did. Expect this to be a source
of divergence in Phase 4 replication, and attribute it correctly.

### 2.2 Ecosystem condition

Per ECT class, from UNSD Tables 13–18. Class B/N unless marked.

| ECT | Layer | Class | Evidence |
|---|---|---|---|
| A1 physical | SoilGrids (bulk density, texture) | **①** | Table 13 |
| A1 | HydroSHEDS; Global Surface Water Explorer | **①** | Table 13 |
| A1 | GRACE (water stocks); UN-IGRAC GGIS / GGMN (groundwater) | **①** | Table 13 |
| A1 | GMIS / GISA impervious surface | **①** | Table 13 |
| A2 chemical | **SoilGrids SOC**; GSDE; FAO GSOC | **①** | Table 13 (SOC), Table 28 |
| A2 | **SEDAC PM2.5 grids** (van Donkelaar) | **①** | Table 14 |
| A2 | GEMStat (SDG 6.3.2: total N, total P, pH, DO) | **①** | Table 14 — station data, sparse |
| B1 compositional | **GLOBIO MSA** | **①** | Table 15, named with mechanism ✅ *have* |
| B1 | **BII / PREDICTS** | **①** | Table 15 (#435) |
| B1 | IUCN Red List; GBIF | **①** | Table 15 — 🔴 IUCN spatial is no-redistribution |
| B2 structural | **GlobBiomass** → successor **ESA CCI Biomass** | **①** *(successor: B)* | Table 16 names GlobBiomass specifically; CCI Biomass is its continuation (#445) |
| B2 | ETH canopy height | **B** | Post-dates guidance (#440) |
| B3 functional | **MODIS NPP (MOD17)**, **Copernicus DMP**, **Copernicus LAI** | **①** | Table 17, with direct product links (#499) |
| C1 landscape | **our own extent account** | **①** | Table 18: *"Ecosystem extent accounts likely form the basis for these indicators"* — this directly endorses the h3-derived approach in #7 |
| C1 | Global Dam Watch; SEDAC gROADS; OpenStreetMap | **①** | Table 18 (barrier density) |
| C1 | FLII; gHM | **B** | Not named; pressure-side proxies (#470, #210) |
| — | Norway Nature Index · South Africa river CI · Peru BILBI/GDM · Mexico EII | **③** | Table 23 — all **national**, none reusable globally |

### 2.3 Ecosystem services

UNSD §6.4 models exactly ten services. Per-service Tier 1 standard:

| Service | Standard Tier 1 | Class | Our pick / gap |
|---|---|---|---|
| **Crop provisioning** | InVEST Crop Production (12 staples statistical / 175 percentile); ARIES uses **SPAM** + **FAOSTAT** year-adjustment, then ecosystem contribution via **Vallecillo et al. 2019** (natural : natural+human inputs, energetic); FAO **GAEZ v4** Theme 4 | **①②** | SPAM 2020 + FAOSTAT (#501) — same method, newer SPAM. ✅ standard-aligned |
| **Wood provisioning** | FAO FRA / FAOSTAT harvest, spatially allocated by observed forest change; ARIES is "the main multi-service platform with this capability" | **①②** | Hansen GFC (#434) + FAO. ✅ aligned |
| **Air filtration** | Deposition × concentration × vegetation; i-Tree and ESTIMAP are the named platforms | **①** | SEDAC PM2.5 (①) + LAI. ✅ aligned |
| **Soil erosion control** | InVEST SDR / LUCI (both compute pixel→stream **connectivity**); **ARIES implements RUSLE** (Martínez-López et al. 2019) | **①②** | **GloSEM = B** (not named, but RUSLE-based so methodologically aligned) |
| **Water supply** | Measure **water abstraction**, not yield — SEEA EA ¶6.103 permits "volume of water abstracted" as the proxy; GRDC for calibration | **①** | ⚠️ our runoff/water-yield framing is **B** and measures the wrong quantity — see §3 |
| **Water purification** | InVEST NDR (terrestrial N/P retention), distinguished from in-stream denitrification | **①** | Global NEWS loading = **B** |
| **Water flow regulation** | InVEST / LUCI / ESTIMAP / Data4Nature | **①** | HydroSHEDS (①) + Aqueduct (**B**) |
| **Global climate regulation** | **IPCC Tier 1 stock-difference**, IPCC default coefficients; ARIES via **Ruesch & Gibbs (2008)** stratified 5 ways; soil C from **ISRIC**; InVEST 4-pool lookup | **①②** | ⚠️ `irrecoverable-carbon` = **B** — see §1.1 |
| **Pollination** | **InVEST crop pollination** (wild bees; index-based, *not empirically validated*); ARIES uses **ESTIMAP** (single generic pollinator); **Klein et al. 2007** dependency ratios | **①②** | Klein + InVEST logic. ✅ aligned |
| **Recreation** | ARIES Explorer: **UNWTO** international-tourist country data spatialized by an **ESTIMAP** landscape-attractiveness model. Tier 2: InVEST geotagged photos — *"covers only the 2005-2017 period and appears to be no longer updated"* | **①②** | ⚠️ Chaplin-Kramer NCP nature-access = **B**, not the standard |

**Documented national practice** (Table 27) — the replication targets: Netherlands (13 services),
UK/ONS, China (Ouyang et al. 2020), EU (Vallecillo/La Notte), Rwanda (Bagstad et al. 2019 — carbon,
sediment, nutrient, water yield), South Africa (Turpie et al. 2021), USA (Warnell et al. 2020).

#### Correction: ARIES platform ≠ ARIES for SEEA Explorer

I earlier said ARIES does "four of ~27 services." That is true of the **Explorer**; it understates the
**platform**. UNSD Table 25 credits the ARIES/k.LAB platform with: crop, grazed biomass, timber, NTFP
(monetary only), water supply, global climate regulation, local climate (index), soil erosion control,
flood mitigation, pollination, recreation. So the gap we're filling is the Explorer's *exposure* and its
lack of scenarios — not a modelling deficit in ARIES.

### 2.4 Monetary

| Need | Class | Note |
|---|---|---|
| Exchange-value concept, resource rent, NPV | **①** | SEEA EA Ch.8–10 — the *method* is fully standardised |
| FAOSTAT producer prices; World Bank commodity prices | **①** | Standard price sources |
| **EXIOBASE** for resource rent / use tables / service trade | **B** | Not named in SEEA EA or the biophysical guidance (which is biophysical only). Check the **Monetary Valuation technical report** (#1) before concluding — it may well name MRIO. |
| **ESVD** value transfer | **B** | SEEA Ch.9.5 sanctions value transfer as a *method*; ESVD is not named as *the* database |
| **ENCORE** dependency ratings | **N** | No SEEA standard for populating the use table's non-zero structure |
| Carbon price | **N** | SEEA permits carbon markets *or* SCC "under appropriate assumptions" — deliberately unresolved. SEEALand's $25/tCO₂ is illustrative, not normative. |
| Discount rate / asset life | **N** | SEEALand uses 2% real / 100 yr as an *example*. No prescribed value. |

**The monetary side is where "no standard exists" is most often the honest answer** — which is exactly
why the assumptions panel and sensitivity ranges in #9 are not optional polish.

---

## 3. Where we knowingly deviate

Declare each of these in the methods record (#12):

1. **Carbon**: `irrecoverable-carbon` instead of IPCC Tier 1 coefficients. **Fix** — implement the IPCC lookup (§1.1).
2. **Water supply**: we framed this as runoff/water yield. SEEA ¶6.103 wants **water abstraction**. Yield is the *input* to the service, not the service. **Fix the framing**, or rename what we report.
3. **Land cover**: GLC_FCS30D over CCI LC trades comparability for resolution (§1.2).
4. **Extent classification**: WTE as the partition is our engineering solution to GET's overlap problem — endorsed as a crosswalk target, not as the reference classification.
5. **Degradation attribution**: we drive degradation from *condition* change; InVEST and ARIES drive carbon change almost entirely from *land-cover* change. A genuine improvement, and a genuine divergence.
6. **Recreation**: NCP nature-access instead of UNWTO × ESTIMAP.
7. **Erosion**: GloSEM instead of a live RUSLE/SDR run — same equation family, no pixel→stream connectivity.

## 4. Ingestible IUCN products

To answer the question directly — what IUCN actually publishes that we can take:

| Product | Ingestible? | Licence |
|---|---|---|
| **GET Level 3 (EFG) indicative maps v2.1** — [Zenodo 10081251](https://zenodo.org/records/10081251), raster GeoTIFF + GeoJSON, ~110 EFGs | ✅ **yes** — queued as data-workflows#438 | 🟢 CC-BY-4.0 |
| **GET EFG descriptive profiles** — the typology text, assembly filters and diagnostics per group | ✅ yes — the reference for the crosswalk (#5) | 🟢 CC-BY-4.0 |
| **IUCN Red List of Ecosystems** assessments | partly — assessment-level, incomplete global coverage; relevant to SEEA Ch.13 thematic accounts and maps onto the "Destroyed" condition descriptor | varies |
| **IUCN habitat classification + Lumbierres 2021 crosswalk** | ✅ queued as data-workflows#427 | check |
| **IUCN Red List species ranges** | 🔴 **no** — `NO` verdict, no redistribution incl. derivatives | 🔴 IUCN ToU |

So: **GET is the ingestible IUCN product, and it is already queued.** The Red List spatial data is the
one that isn't, and that constraint is already recorded in the catalog's licence inventory.
