# Layer provenance: why each layer is in the app

The planned layer list for unseea, and the justification for each. One question per row: **is this the
choice SEEA analyses actually make, or our own judgement call?**

Companion to [`DATA.md`](DATA.md) (acquisition and licensing) and [`DESIGN.md`](DESIGN.md) (design).

## Why this matters

Two of our differentiators — *replication and validation* against published accounts, and *agreeing with
ARIES where both can compute the same account* — only work if we know where we deviate. A layer that is
better in the abstract but different from what everyone else used produces a divergence we cannot
attribute. Conceptual quality and comparability are **different axes**, and for a statistical standard
comparability often wins.

## Evidence classes

| Class | Meaning |
|---|---|
| **①** | **Named in SEEA EA or the UNSD Guidelines on Biophysical Modelling** as a recommended source, model or reference classification. The closest thing to a standard that exists. |
| **②** | **Used by ARIES for SEEA** — the reference implementation's actual choice. |
| **③** | **Used in a published national/regional SEEA compilation** (UNSD Tables 10, 23, 27). Documented practice. |
| **B** | **Best-available — our judgement.** No standard exists, or the standard is superseded/unusable at global scale. Declare it in the methods record. |
| **N** | **No standard exists** for this step. Every compiler improvises. |

A row can hold several. **①②③ together is as strong as this domain gets.**

**Status** — ✅ in the catalog · ⏳ on the roadmap, with the issue that tracks it.

Sources, all in [`research/`](research/): **SEEA EA (official 2024 ed., ST/ESA/STAT/SER.F/124)**; **UNSD Monetary
Valuation of Ecosystem Services and Assets** (2022, 137 pp); **UNSD Guidelines on Biophysical
Modelling (2022)** — Table 5 (land cover products), 10 (country extent practice), 13–18 (condition
indicators per ECT class), 23 (country condition practice), 25 (ES platform capability), 26 (pollination
dependence), 27 (country ES practice), 28 (major data sources), and §6.4.1–6.4.10 per service.

---

## 1. Spatial units and accounting areas

| Layer | Class | Evidence | Status |
|---|---|---|---|
| **UN M49 administrative entities** | **①②** | The EAA unit ARIES for SEEA offers; the official statistical reporting geography | ⏳ [#19](https://github.com/SchmidtDSE/unseea/issues/19) |
| **FAO hydrological basins** | **②** | ARIES's basin EAA option | ⏳ [#19](https://github.com/SchmidtDSE/unseea/issues/19) |
| Overture divisions (country/region/county) | **B** | Our EAA workhorse — finer and better-maintained, but not the official reporting geography | ✅ |
| HydroSHEDS / HydroBASINS | **①** | UNSD Tables 13, 28 | ⏳ dw#442, dw#223 |
| USGS WBD (HUC2–12) | **B** | US basins, no global standing | ✅ |
| WWF terrestrial ecoregions · MEOW | **B** | Not an EAA type in the standard. Our use is **reference-level stratification** (§2) and crosswalk tie-breaking | ✅ |
| Protected areas (WDPA / PAD-US) | **①** | SEEA EA §3.2.3 names protected areas as an EAA type; basis of the Ch.13 thematic PA accounts | ✅ (🔴 licence — [#14](https://github.com/SchmidtDSE/unseea/issues/14)) |

Ingesting **UN M49** is the same reasoning as CCI LC below: for replication work, matching the reporting
geography published accounts used is worth more than a finer boundary set.

## 2. Ecosystem extent

| Layer | Class | Evidence | Status |
|---|---|---|---|
| **IUCN GET Level 3 (EFG)** | **①②** | SEEA EA Table 3.2 adopts GET as the **SEEA Ecosystem Type reference classification**; Table 4.1 compiles at "Level 3 – EFG". ARIES uses GET for extent | ⏳ dw#438 |
| **ESA CCI Land Cover 300 m** | **①③** | UNSD Table 5; §4.4.3 ¶131 calls it "the best available time series of land cover data products". Annual 1992–2022+. Widely used in national practice | ⏳ dw#498 |
| **World Terrestrial Ecosystems** (Sayre) | **①** *(weak)* | SEEA EA §3.67 names it among classifications for which "correspondences… will be developed" — endorsed as a crosswalk target, not as the reference classification. Our use of it as the wall-to-wall partition is an engineering choice | ⏳ dw#438 |
| **GLC_FCS30D 30 m** | **B** | Post-dates all guidance. Higher resolution and purpose-built for land-cover *dynamics*; carries no comparability claim | ⏳ dw#498 |
| Copernicus CGLS-LC100 100 m | **①** | UNSD Table 5. Single year, so snapshot-only | ✅ |
| NLCD Annual + Land Cover Change | **B** | US national product, no global standing; the only true annual change series we can reach today | ⏳ dw#453 |
| **Hansen Global Forest Change** | **①** | UNSD Table 6, §4.4.3 ¶131 — forest extent change | ⏳ dw#434 |
| **JRC Global Surface Water** | **①** | UNSD §4.4.3 ¶131 ("Surface Water Explorer"), Table 13 | ⏳ dw#441 |
| Global Mangrove Watch · Allen Coral Atlas | **B** | Not named; best-available for MFT1 / M1 ecosystem types | ⏳ dw#443, dw#444 |
| FAO LCCS classification | **③** | Uganda and others (Table 10) | n/a — classification |

**Two products, two jobs.** CCI LC is the **conformance baseline** for replication (Phase 4); GLC_FCS30D
carries fine-grained scenario work and small EAAs. If only one lands first, CCI LC is both safer and much
cheaper (300 m vs 30 m, global, annual).

⚠️ **No country in Table 10 used IUCN GET.** Documented practice used FAO LCCS (Uganda), Holdridge life
zones (Guatemala), and national forest maps. GET is the standard by the standard's own designation and by
ARIES's implementation, but not yet by practice — expect an attributable divergence in Phase 4.

## 3. Ecosystem condition

Per ECT class, from UNSD Tables 13–18.

| ECT | Layer | Class | Evidence | Status |
|---|---|---|---|---|
| A1 physical | **SoilGrids 2.0** (bulk density, texture) | **①** | Table 13 | ⏳ dw#446 |
| A1 | **HydroSHEDS** · **Global Surface Water Explorer** | **①** | Table 13 | ⏳ dw#442, dw#441 |
| A1 | GRACE (water stocks) · UN-IGRAC GGIS/GGMN (groundwater) | **①** | Table 13 | ⏳ |
| A1 | GMIS / GISA impervious surface | **①** | Table 13 | ⏳ |
| A2 chemical | **SoilGrids SOC** · GSDE · FAO GSOC | **①** | Table 13, Table 28 | ⏳ dw#446 |
| A2 | **SEDAC PM2.5 grids** (van Donkelaar) | **①** | Table 14 | ⏳ [#19](https://github.com/SchmidtDSE/unseea/issues/19) |
| A2 | GEMStat (SDG 6.3.2: total N, total P, pH, DO) | **①** | Table 14 — station data, sparse | ⏳ |
| B1 compositional | **GLOBIO MSA** | **①** | Table 15, named with mechanism. Reference level built in ([0,1] vs undisturbed) | ✅ |
| B1 | **Biodiversity Intactness Index / PREDICTS** | **①** | Table 15 | ⏳ dw#435 |
| B1 | IUCN Red List · GBIF | **①** | Table 15 | ✅ (🔴 IUCN spatial) |
| B2 structural | **ESA CCI Biomass** *(successor to GlobBiomass)* | **①** *(successor: B)* | Table 16 names **GlobBiomass** specifically; CCI Biomass continues it | ⏳ dw#445 |
| B2 | ETH canopy height 10 m | **B** | Post-dates guidance | ⏳ dw#440 |
| B3 functional | **MODIS NPP (MOD17)** · **Copernicus DMP** · **Copernicus LAI** | **①** | Table 17, with direct product links | ⏳ dw#499 |
| C1 landscape | **derived from our own extent account** | **①** | Table 18: *"Ecosystem extent accounts likely form the basis for these indicators"* — direct endorsement of the h3 approach | ⏳ [#7](https://github.com/SchmidtDSE/unseea/issues/7) |
| C1 | Global Dam Watch · SEDAC gROADS · OpenStreetMap | **①** | Table 18 (barrier density) | ⏳ |
| C1 | FLII · gHM | **B** | Not named; pressure-side proxies | ⏳ dw#470, dw#210 |

**Reference levels: N.** SEEA offers five candidate reference conditions and seven estimation methods
(Table 5.9) and prescribes none. Every documented condition account uses **national data and a bespoke
index** — Norway's Nature Index, South Africa's river Condition Index, Peru's BILBI/GDM, Mexico's
Ecosystem Integrity Index (Table 23). None is reusable globally. Our default — **ecoregion × ET ambient
percentiles** — is class **B**, chosen because it is one of only two methods tractable at global scale
(the other being prescribed levels). This is the single least-standardised part of the biophysical work,
and the reason reference levels must be inspectable and overridable ([#6](https://github.com/SchmidtDSE/unseea/issues/6)).

Worth noting how much of this class is ①: GLOBIO, BII, SoilGrids, MODIS NPP / Copernicus DMP and the
h3-derived C1 metrics are all named in the guidance. The **variables** are well-standardised even though
the **reference levels** are not.

## 4. Ecosystem services

UNSD §6.4 models exactly ten services; those ten are our target ([#8](https://github.com/SchmidtDSE/unseea/issues/8)).

| Service | Planned approach | Class | Evidence | Status |
|---|---|---|---|---|
| **Crop provisioning** | **SPAM** production × **FAOSTAT** year-adjustment → ecosystem contribution via **Vallecillo et al. 2019** (natural : natural+human inputs, energetic) | **①②** | §6.4.1.3 ¶217 — exactly ARIES's method. FAO **GAEZ v4** Theme 4 also named | ⏳ dw#501 |
| **Wood provisioning** | FAO FRA / FAOSTAT harvest, spatially allocated by observed forest change | **①②** | §6.4.2.3 ¶235–237 | ⏳ dw#434 |
| **Air filtration** | Deposition × concentration × vegetation cover (i-Tree / ESTIMAP logic); **SEDAC PM2.5** + LAI | **①** | §6.4.3, Table 14 | ⏳ [#19](https://github.com/SchmidtDSE/unseea/issues/19) |
| **Soil erosion control** | RUSLE family: retention = potential − actual loss | **①②** | §6.4.4.3 ¶261 — ARIES implements RUSLE (Martínez-López et al. 2019); InVEST SDR / LUCI add pixel→stream connectivity | ⏳ |
| ↳ *via* **GloSEM** | import a published RUSLE output rather than routing in-app | **B** | Not named; methodologically aligned, but no connectivity term | ⏳ [#19](https://github.com/SchmidtDSE/unseea/issues/19) |
| **Water supply** | **Water abstraction** — not yield | **①** | SEEA EA ¶6.103; UNSD ¶266–268: "measurement focus … lies on estimating water abstraction". Flow regulation and purification are *inputs to* this service | ⏳ [#8](https://github.com/SchmidtDSE/unseea/issues/8) |
| **Water purification** | InVEST NDR terrestrial N/P retention, distinguished from in-stream denitrification | **①** | §6.4.6.2 ¶286–287 | ⏳ |
| ↳ *via* Global NEWS loading | | **B** | Not named | ⏳ [#19](https://github.com/SchmidtDSE/unseea/issues/19) |
| **Water flow regulation** | Baseflow / peak-flow attenuation over HydroSHEDS | **①** | Table 25 (InVEST, LUCI, ESTIMAP, Data4Nature) | ⏳ dw#442, dw#433 |
| **Global climate regulation** | **IPCC Tier 1 stock-difference**: IPCC 2006 default densities stratified per **Ruesch & Gibbs (2008)** by land cover × ecofloristic region × continent × frontier forest × recent fire; soil carbon from **SoilGrids**. Plus the **removal flux** | **①②** | §6.4.8.3 ¶311–314 — the Tier structure follows the IPCC Guidelines; ¶314 describes ARIES's implementation | ⏳ [#21](https://github.com/SchmidtDSE/unseea/issues/21), dw#500 |
| **Pollination** | InVEST/ESTIMAP pollinator abundance × **Klein et al. 2007** crop dependency | **①②** | §6.4.9.3 ¶329; Table 26. *Both models are index-based and explicitly not empirically validated* | ⏳ |
| **Recreation** | **UNWTO** international-tourist statistics spatialized by an **ESTIMAP** landscape-attractiveness model; population proximity for local recreation | **①②** | §6.4.10.3 ¶343 — ARIES Explorer's actual Tier 1 | ⏳ [#19](https://github.com/SchmidtDSE/unseea/issues/19) |
| ↳ *alt* Chaplin-Kramer NCP nature-access | | **B** | Not named | ⏳ |
| Grazed biomass *(beyond the ten)* | **GLW 4** livestock density + forage | **②** | Table 25 credits ARIES | ⏳ dw#447 |

Metric note: recreation's headline unit is **number of visits**; UNSD ¶348 observes visit *length* is
arguably better but needs GPS data that raises privacy problems. Non-resident visits are recorded as
**exports** (SEEA §7.2.6).

**Replication targets** (Table 27): Netherlands (Horlings et al. 2019, 13 services), UK/ONS 2019, China
(Ouyang et al. 2020), EU (Vallecillo/La Notte), Rwanda (Bagstad et al. 2019), South Africa (Turpie et al.
2021), USA (Warnell et al. 2020).

**ARIES platform ≠ ARIES for SEEA Explorer.** UNSD Table 25 credits the ARIES/k.LAB *platform* with
eleven services — crop, grazed biomass, timber, NTFP (monetary only), water supply, global climate
regulation, local climate (index), soil erosion control, flood mitigation, pollination, recreation. The
*Explorer* exposes four to five. The gap we fill is the Explorer's **exposure and its lack of scenarios**,
not a modelling deficit in ARIES.

## 5. Monetary

| Need | Class | Evidence |
|---|---|---|
| Exchange-value concept, resource rent, NPV | **①** | SEEA EA Ch.8–10 — the *method* is fully standardised, even where the inputs are not |
| FAOSTAT producer prices · World Bank commodity prices | **①** | Standard price sources |
| **EXIOBASE** — resource rent, use tables, service imports/exports | **B** *(confirmed)* | **Checked:** the Monetary Valuation report mentions EXIOBASE, MRIO, input-output and multi-regional **zero times** in 137 pages. No standard names an MRIO for this, so our pick is genuinely our own judgement — reasonable, and to be declared |
| **ESVD** value transfer | **①** | The UNSD Monetary Valuation report devotes a worked section to it — *"Demonstrating the use of data from the ecosystem services literature: the Ecosystem Services Valuation Database example"* (p.110) — and builds its Table 1 of valuation approaches from SEEA EA + ESVD + **ISO 14008**. **EVRI** is named as a second such database |
| **ENCORE** dependency ratings | **N** | No SEEA standard for populating the use table's non-zero structure |
| Carbon price | **N** | SEEA permits carbon markets *or* SCC "under appropriate assumptions" — deliberately unresolved. SEEALand's $25/tCO₂ is illustrative |
| Discount rate · asset life | **N** | SEEALand's 2% real / 100 yr is an example, not a prescription |

The monetary side is where **N** is most often the honest answer — which is why the assumptions panel and
sensitivity ranges in [#9](https://github.com/SchmidtDSE/unseea/issues/9) are not optional polish.

## 6. Deviations to declare

Each of these goes in the methods record ([#12](https://github.com/SchmidtDSE/unseea/issues/12)):

1. **Extent classification** — WTE as the wall-to-wall partition is our engineering answer to GET's overlapping indicative maps; endorsed as a crosswalk target, not as the reference classification.
2. **Land cover** — where GLC_FCS30D is used instead of CCI LC, resolution is bought at the cost of comparability.
3. **Reference levels** — ecoregion × ET ambient percentiles, where documented practice uses national indices.
4. **Degradation attribution** — we drive degradation from *condition* change. UNSD ¶315 notes InVEST and ARIES drive carbon change almost entirely from *land-cover* change, handling only frontier forests. A genuine improvement, and a genuine divergence.
5. **Erosion** — an imported RUSLE product (GloSEM) rather than a live SDR run, so no pixel→stream connectivity term.
6. **Recreation** — if NCP nature-access is used instead of UNWTO × ESTIMAP.
7. **Scale** — Tier 1 global inputs throughout, recorded per service and per variable.

## 7. Ingestible IUCN products

| Product | Ingestible? | Licence |
|---|---|---|
| **GET Level 3 (EFG) indicative maps v2.1** — [Zenodo 10081251](https://zenodo.org/records/10081251), ~110 EFGs, raster + vector | ✅ **yes** — dw#438 | 🟢 CC-BY-4.0 |
| **GET EFG descriptive profiles** — typology text, assembly filters, diagnostics | ✅ yes — the crosswalk reference ([#5](https://github.com/SchmidtDSE/unseea/issues/5)) | 🟢 CC-BY-4.0 |
| **IUCN Red List of Ecosystems** assessments | partly — assessment-level, incomplete global coverage. Relevant to Ch.13 thematic accounts; "ecosystem collapse" maps onto SEEA's "Destroyed" condition descriptor | varies |
| **IUCN habitat classification + Lumbierres 2021 crosswalk** | ✅ dw#427 | check |
| **IUCN Red List species ranges** | 🔴 **no** — no redistribution incl. derivatives | 🔴 IUCN ToU |

**GET is the ingestible IUCN product, and it is already queued.**

---

### Footnotes on layers we hold that are not the accounting choice

- **`irrecoverable-carbon`** (Noon et al. 2022) is a conservation-prioritisation construct — carbon both *manageable* and *unrecoverable within 30 years* — so by design it is not a total accounting stock and cannot fill the global climate regulation row. Retain it as a **secondary/thematic** layer for targeting. The accounting path is the IPCC Tier 1 lookup above ([#21](https://github.com/SchmidtDSE/unseea/issues/21)).
- **`nci-frontiers`** supplies crop, grazing and forestry *revenue densities*. Revenue is not the ecosystem contribution; it needs the Vallecillo/resource-rent step before it can enter an account. Useful as a cross-check on SPAM-derived values.
- **`gfw-fishing-effort`** is fishing *effort*, not catch — a proxy for wild-fish provisioning, and 🟠 NC.
