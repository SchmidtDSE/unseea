# SEEA EA reference extract

Distilled from the SEEA Ecosystem Accounting (2021) White Cover, 393 pp. Sources in this directory:

- `seea_ea_white_cover_final.pdf` — the standard as published by UNSD.
- `seea-ea-fulltext.txt` — text extraction, `===PAGE n===` delimited (PDF page numbers, which run ~22
  ahead of the printed page numbers used in the standard's own cross-references).

This file holds the controlled vocabularies and table structures the app must conform to. It is the
source for `system-prompt.md` and for the versioned lookup tables described in
[`../DESIGN.md`](../DESIGN.md) §6.1. Keep it faithful to the standard; put our own choices in DESIGN.md.

---

## 1. The five accounts (Table 2.1)

| # | Account | Terms | Chapter |
|---|---|---|---|
| 1 | Ecosystem extent account | physical | 4 |
| 2 | Ecosystem condition account | physical | 5 |
| 3 | Ecosystem services flow account | physical | 7 |
| 4 | Ecosystem services flow account | monetary | 9 |
| 5 | Monetary ecosystem asset account | monetary | 10 |

Chapter 11 integrates these into extended supply-use tables and balance sheets; Ch. 13 adds thematic
accounts (biodiversity, carbon, ocean, urban); Ch. 14 covers derived indicators.

## 2. Spatial units (Ch. 3)

- **BSU** — basic spatial unit; the finest tessellation accounts are built up from.
- **ET** — ecosystem type; reference classification is IUCN GET, compiled at Level 3 (EFG).
- **EA** — ecosystem asset; a contiguous, *mutually exclusive (non-overlapping)* area of one ET.
- **EAA** — ecosystem accounting area; the reporting boundary (country, state, river basin, PA).

Scale invariance, footnote 172 — the licence for H3 aggregation:

> "an area-weighted approach has been used meaning that the overall index is invariant to whether the
> data are collated at finer resolutions (e.g. pixels) or at larger resolutions (e.g. for the ecosystem
> asset)."

## 3. SEEA Ecosystem Type reference classification (Table 3.2) — IUCN GET biomes

| Realm | Biomes |
|---|---|
| Terrestrial | T1 Tropical–subtropical forests · T2 Temperate–boreal forests & woodlands · T3 Shrublands & shrubby woodlands · T4 Savannas and grasslands · T5 Deserts and semi-deserts · T6 Polar-alpine · T7 Intensive land-use systems |
| Freshwater | F1 Rivers and streams · F2 Lakes · F3 Artificial fresh waters |
| Marine | M1 Marine shelfs · M2 Pelagic ocean waters · M3 Deep sea floors · M4 Anthropogenic marine systems |
| Subterranean | S1 Subterranean lithic · S2 Anthropogenic subterranean voids |
| Transitional | TF1 Palustrine wetlands · FM1 Semi-confined transitional waters · MT1 Shoreline systems · MT2 Supralittoral coastal systems · MT3 Anthropogenic shorelines · MFT1 Brackish tidal systems · SF1 Subterranean freshwaters · SF2 Anthropogenic subterranean freshwaters · SM1 Subterranean tidal |

25 biomes, 5 realms. Level 3 (EFG) is ~110 groups. Source: Keith et al. (2020).

Note the standard's flexibility clause on Table 4.1: *"Compilation will require the use of nationally
selected ecosystem types."* Conformance means crosswalkable to GET, not identical to it.

## 4. Ecosystem extent account (Table 4.1)

Rows are accounting entries, columns are ETs, cells are area:

```
Opening extent
Additions to extent
    Managed expansion
    Unmanaged expansion
Reductions in extent
    Managed reductions
    Unmanaged reductions
Net change in extent
Closing extent
```

Where managed/unmanaged cannot be distinguished, record only the total. Complementary presentations:
**ET change matrix** (Table 4.2, opening rows × closing columns, unchanged area on the diagonal) and
**extent by type of economic unit** (Table 4.4).

## 5. Ecosystem Condition Typology (Table 5.1)

| Group | Class | Content |
|---|---|---|
| A Abiotic | A1 Physical state | physical descriptors of abiotic components (soil structure, water availability) |
| | A2 Chemical state | chemical composition of abiotic compartments (soil nutrients, water quality, air pollutants) |
| B Biotic | B1 Compositional state | composition/diversity of ecological communities (presence/abundance of key species) |
| | B2 Structural state | aggregate properties (total biomass, canopy coverage, annual max NDVI) |
| | B3 Functional state | summary statistics of interactions (primary productivity, community age, disturbance frequency) |
| C Landscape | C1 Landscape/seascape | mosaics at coarse scale (landscape diversity, connectivity, fragmentation) |

Three nested accounts: **variable** (raw values, Table 5.2) → **indicator** (rescaled [0,1] against
lower and upper reference levels, Table 5.3) → **index** (weighted, Table 5.4–5.6). SEEALand weights
each of 6 ECT classes equally (0.17), and equally weights variables within a class.

### 5.1 Example variables by ET (Table 5.7, abridged)

| ET | A1 Physical | A2 Chemical | B1 Compositional | B2 Structural | B3 Functional | C1 Landscape |
|---|---|---|---|---|---|---|
| T1 Tropical–subtropical forests | soil water availability in driest quarter; wetness | soil organic carbon; leaf & litter N | tree species richness; bird species richness | tree cover density; dominant tree height; canopy layers; deadwood volume; forest age classes | dry matter productivity; seed-dispersing species; water stress index | forest area density; landscape diversity; forest connectivity; edge:interior ratio |
| T2 Temperate–boreal forests | vegetation water content (NDWI) | soil organic carbon; air pollutants; foliar & litter N | tree, lichen, bird species richness | forest floor depth; tree cover density; deadwood volume; age classes | dry matter productivity; nesting hollows; top predators; NDVI; water stress | forest area density; landscape diversity; connectivity |
| T3 Shrublands | % burnt area; soil layer thickness | soil organic carbon; soil P | bird species richness | tree cover density | dry matter productivity; re-sprouting species share | landscape diversity; shrubland/forest connectivity |
| T4 Savannas & grasslands | % bare ground | soil organic carbon; soil pH | bird & butterfly richness; non-native share | tree/shrub presence & density | dry matter productivity; termite mound abundance | tree connectivity; grassland connectivity |
| T5 Deserts & semi-deserts | water availability; surface crusting | soil pH | reptile diversity/abundance | vegetation cover | viable seed density in soil | spatial distribution of waterholes |

### 5.2 Reference conditions (Tables 5.8, 5.9)

Five candidate reference conditions — for **natural** ecosystems: undisturbed/minimally-disturbed,
historical, least-disturbed; for **anthropogenic**: contemporary, best-attainable.

Estimation methods and which reference conditions they support:

| Method | Undisturbed | Historical | Least-disturbed | Contemporary | Best-attainable |
|---|---|---|---|---|---|
| 1 Reference sites | x | x | x | x | |
| 2 Modelled reference conditions | x | x | x | | x |
| 3 Statistical, ambient distributions | | | x | | x |
| 4 Historical & paleo-environmental data | | x | | | |
| 5 Contemporary data | | | | x | |
| 6 Prescribed levels | | | | | x |
| 7 Expert opinion | x | | x | | x |

**Prohibition:** do not average condition across ETs with different reference conditions —

> "An average measure of ecosystem condition across all ET has not been derived as this would imply
> aggregation across different reference conditions and this is not recommended."

## 6. Reference list of selected ecosystem services (Table 6.3)

Asterisk marks services SEEA flags with specific treatment guidance in §6.4.

### Provisioning

| Service | Definition (condensed) | Final/intermediate |
|---|---|---|
| Crop provisioning* | ecosystem contributions to growth of cultivated plants harvested for food, fibre, fodder, energy | final |
| Grazed biomass provisioning* | contributions to growth of grazed biomass input to livestock; excludes fodder crops | final (may be intermediate to livestock) |
| Livestock provisioning* | contributions to growth of cultivated livestock and products | final; **not recorded separately if grazed biomass is recorded as final** |
| Aquaculture provisioning | contributions to growth of animals/plants in aquaculture facilities | final |
| Wood provisioning | contributions to growth of trees and woody biomass, plantation and uncultivated; excludes NWFP | final |
| Wild fish & other natural aquatic biomass | contributions to growth of fish/aquatic biomass captured in uncultivated contexts | final |
| Wild animals, plants & other biomass | contributions to wild biomass incl. NWFP, hunting, trapping, bio-prospecting; excludes wild fish | final |
| Genetic material | contributions from biota used for breeding, gene synthesis, product development | **usually intermediate** |
| Water supply* | combined contributions of flow regulation, purification etc. to water of appropriate quality | final |

### Regulating and maintenance

| Service | Definition (condensed) | Final/intermediate |
|---|---|---|
| Global climate regulation | reducing atmospheric GHG via **removal (sequestration)** and **retention (storage)** of carbon | final |
| Rainfall pattern regulation (sub-continental) | vegetation maintaining rainfall via evapotranspiration and moisture recycling | final or intermediate |
| Local (micro/meso) climate regulation | regulation of ambient conditions via vegetation — urban green/blue space, shade | final or intermediate |
| Air filtration | deposition, uptake, fixing, storage of air-borne pollutants | usually final |
| Soil quality regulation | decomposition of materials; soil fertility and characteristics | **usually intermediate** |
| Soil erosion control | stabilising effects of vegetation reducing soil/sediment loss | final or intermediate |
| Landslide mitigation | stabilising effects preventing damage from mass wasting | final |
| Solid waste remediation | transformation of organic/inorganic substances by biota | final or intermediate |
| Water purification — nutrients / other pollutants | breakdown or removal of nutrients and pollutants in surface and groundwater | final or intermediate |
| Water flow regulation — baseline flow maintenance | absorbing, storing and gradually releasing water to secure regular flow | final or intermediate |
| Water flow regulation — peak flow mitigation | absorbing and storing water, mitigating floods; supplied with river flood mitigation | final |
| Flood control — coastal protection | linear seascape elements (reefs, dunes, mangroves) mitigating surges and storms | final |
| Flood control — river flood mitigation | riparian vegetation as physical barrier to high water | final |
| Storm mitigation | vegetation mitigating wind, sand and other (non-water) storms | final |
| Noise attenuation | reduction of noise impact on people | usually final |
| Pollination | wild pollinators fertilising crops | final or intermediate |
| Biological control — pest control | reducing incidence of species affecting biomass production | final or intermediate |
| Biological control — disease control | reducing incidence of species affecting human health | usually final |
| Nursery population & habitat maintenance | sustaining populations via habitat maintenance and gene-pool protection | **intermediate** |

### Cultural

| Service | Definition (condensed) | Final/intermediate |
|---|---|---|
| Recreation-related | biophysical qualities enabling direct, in-situ, physical and experiential interaction; locals and visitors; incl. recreational fishing and hunting | final |
| Visual amenity* | contributions to local living conditions through sensory, especially visual, benefits | final |
| Education, scientific and research | qualities enabling intellectual interaction with the environment | final |
| Spiritual, artistic and symbolic | qualities recognised for cultural, historical, aesthetic, sacred or religious significance | final |

Each list also carries an open "Other provisioning / Other regulating and maintenance" residual class.

**Aggregate:** Gross Ecosystem Product (GEP) = value of all final ecosystem services less net imports of
intermediate services.

## 7. Physical and monetary service flow accounts (Ch. 7, 9)

Supply and use tables. Rows are services from the reference list. Supply columns are the supplying
ETs, split resident (inside the EAA) vs non-resident (outside). Use columns are economic units:
industries, households, government, accumulation, and exports.

Recording rules that matter: only final services enter the aggregate; intermediate services between
ecosystem assets are recorded separately and netted; imports/exports of services are explicit
(Ch. 7.2.6); measurement baselines for regulating services are set per Table 7.7.

## 8. Monetary valuation (Ch. 8–10)

**Concept: exchange values**, SNA-consistent. Welfare values, consumer surplus and most
stated-preference estimates belong in the Ch. 12 bridge table, not the core accounts.

Technique families (Ch. 9.3), in the standard's own order of preference: directly observable prices →
prices from markets for similar goods → prices embodied in market transactions (hedonic, production
function, residual value / resource rent) → revealed expenditure (travel cost, averting behaviour) →
expected expenditure (replacement cost) → other.

**SEEALand assumed prices** (Annex, for the worked example):

| Service | Price |
|---|---|
| Wood provisioning | $60 / m³ |
| Crop provisioning | $75 / tonne |
| Wild fish biomass provisioning | $350 / tonne |
| Global climate regulation | $25 / tonne CO₂ |
| Water purification | $100 / tonne N removed |
| Recreation-related | $5 / visit |

**Monetary ecosystem asset account** (Table 10.1) — NPV of expected future service flows. SEEALand
assumptions: asset life **100 years**, discount rate **2% real**, income at period end, constant flows
and prices over asset life except where changed expectations are recorded.

Change in asset value decomposes (Annex 10.1) into: additions (managed/unmanaged expansion), reductions,
**degradation** (condition decline reducing expected future flows), **enhancement**, ecosystem
**conversions**, and **revaluation** (changed expected prices).

## 9. SEEALand worked example (Annex) — the Phase 1 replication fixture

EAA: 250 ha, accounting period 1 Jan – 31 Dec 2020, grid of 10-ha cells. Six ETs:

| # | IUCN GET biome / EFG | Label | Opening ha | Closing ha |
|---|---|---|---|---|
| 1 | T2 / T2.2 Deciduous temperate forests | Forest | 40 | 38 |
| 2 | F2 / F2.1 Large permanent freshwater lakes | Lake | 30 | 30 |
| 3 | T7 / T7.1 Annual croplands | Cropland | 60 | 62 |
| 4 | T7 / T7.4 Urban and industrial ecosystems | Urban area | 50 | 50 |
| 5 | TF1 / TF1.3 Permanent marshes | Wetland | 20 | 20 |
| 6 | M1 / M1.1 Seagrass meadows | Seagrass | 50 | 50 |

One change: **2 ha forest → cropland**, recorded as a managed expansion of cropland and a managed
reduction of forest. Net change in extent totals zero, closing total 250 ha.

Condition indices (Table A.5):

| Entry | Forest | Lake | Cropland | Urban | Wetland | Seagrass |
|---|---|---|---|---|---|---|
| Opening condition | 0.67 | 0.63 | 0.47 | 0.50 | 0.59 | 0.45 |
| Δ abiotic | −0.01 | +0.02 | 0.00 | +0.01 | −0.02 | −0.03 |
| Δ biotic | −0.03 | +0.03 | +0.01 | −0.02 | 0.00 | −0.03 |
| Δ landscape | −0.03 | 0.00 | 0.00 | −0.01 | −0.01 | −0.02 |
| Net change | −0.06 | +0.05 | 0.00 | −0.02 | −0.04 | −0.08 |
| Closing condition | 0.61 | 0.67 | 0.47 | 0.49 | 0.56 | 0.37 |

Forest, lake, wetland and seagrass use **natural** reference conditions; cropland and urban use
**anthropogenic** ones. Forest condition falls mostly through **forest area density**, a connectivity
proxy — i.e. the C1 landscape class carries the conversion signal, which is the mechanism our scenario
engine depends on.

Forest NPV worked example (Table A.10):

| | Opening | Closing |
|---|---|---|
| Wood provisioning | 150 m³ @ $60 | 120 m³ @ $65 |
| Global climate regulation | 160 t CO₂ @ $25 | 125 t CO₂ @ $26 |
| Recreation-related | 1 600 visits @ $5 | 1 450 visits @ $5 |
| Annual exchange value | $21 000 | $18 300 |
| **NPV total** | **$905 065** | **$788 700** |
| Change in NPV | | **−$116 366** |

**GEP for SEEALand = $83,125** (no intermediate services in this example).

Qualitative results to reproduce: degradation recorded for forest, wetland and seagrass; the
forest→cropland conversion is net negative on asset value; revaluation affects every ET except cropland,
whose single service's price did not change; the lake holds the largest share of total asset value.

A complementary spreadsheet published with the standard (`seea.un.org/ecosystem-accounting`) holds the
per-variable condition workings and the NPV-by-ET sheets. **Fetch it before Phase 1** — it contains the
cell-level numbers this table only summarises.

## 10. Things the standard explicitly warns about

- Do not average condition across ETs with different reference conditions (§5.4.1).
- Do not double-count intermediate services in the aggregate (§6.2.3, §7.2.4).
- Ecosystem services are the ecosystem's *contribution*, not the total value of the output (§6.2.1).
- Monetary values "cannot be interpreted as reflecting a complete or universal measure of the value of
  nature since it excludes a range of values, such as intrinsic values" (Annex).
- Monetary valuation "is by no means a necessary feature of ecosystem accounting" — physical-only
  accounts are legitimate and common.
- Where conversions are large or the EAA is small, measure condition separately for the unchanged and
  converted areas rather than relying on extent-sensitive variables (§5.5.5).
