# Source documents

Primary sources for the design, checked in so the analysis is reproducible and citations trace to a page.
All are freely redistributable UN publications.

## The standard

| File | What |
|---|---|
| `seea_ea_final_2024.pdf` | **SEEA Ecosystem Accounting — official published edition**, ST/ESA/STAT/SER.F/124, United Nations, New York, 2024. 443 pp. **Cite this one.** |
| `seea-ea-2024-fulltext.txt` | Text extraction, `===PAGE n===` delimited |
| `seea_ea_white_cover_final.pdf` | The **2021 White Cover** pre-publication draft, 393 pp. Retained because the early analysis was transcribed from it |
| `seea-ea-fulltext.txt` | Text extraction of the White Cover |

⚠️ **Edition note.** The published 2024 edition was copy-edited relative to the White Cover: **content and
structure are stable, wording is not**, and page/footnote numbering shifted (443 pp vs 393 pp). Quotes in
[`../PROVENANCE.md`](../PROVENANCE.md), [`../DESIGN.md`](../DESIGN.md) and `seea-ea-reference.md` have been
re-verified against the 2024 edition where load-bearing. Two known renumberings:

- The scale-invariance statement that justifies our H3 approach was White Cover **footnote 172**; in the
  2024 edition it is **Annex I, Table AI.5, footnote c**.
- The prohibition on averaging condition across ecosystem types is reworded ("across all ecosystem types
  … which is not recommended"), same meaning.

If you find a quote that doesn't grep in `seea-ea-2024-fulltext.txt`, check the White Cover extraction
before assuming it's wrong.

## Guidance and technical reports

| File | What |
|---|---|
| `unsd_guidelines_biophysical_modelling_2022.pdf` | **UNSD Guidelines on Biophysical Modelling for Ecosystem Accounting** (2022), 221 pp. Defines the **Tier 1/2/3** scheme; per-service model and data recommendations for ten services (§6.4); condition-indicator tables per ECT class (13–18); country practice tables (10, 23, 27) |
| `unsd-biophysical-modelling-fulltext.txt` | Text extraction |
| `unsd_monetary_valuation_techreport_2022.pdf` | **Monetary Valuation of Ecosystem Services and Assets for Ecosystem Accounting** — interim version, 1st edition (NCAVES/MAIA, 2022), 137 pp. Valuation methods in SEEA's order of preference, resource rent, value transfer, and the **ESVD worked example** (p.110) |
| `unsd-monetary-valuation-fulltext.txt` | Text extraction |

## Official SEEA supplements

| Path | What |
|---|---|
| `seea_ea_seealand_stylised_example.xlsx` | The **SEEALand worked example** — 15 sheets: extent account, change matrix, condition Stages 1–3, condition indices, ES flows, physical & monetary SUTs, NPV by ET, **NPV decomposition**, monetary asset account |
| `seealand-fixture/*.csv` | The above, one CSV per sheet — the **Phase 1 test fixture** ([#3](https://github.com/SchmidtDSE/unseea/issues/3)) |
| `seea_ea_es_reference_list_crosswalk.xlsx` | Official crosswalk: SEEA services → **CICES v5.1 · NESCS · IPBES · MA · TEEB**, with SEEA codes |
| `seea_ea_es_logic_chains.xlsx` | Ecosystem services logic chains |
| `seea-supplements/*.csv` | Both of the above as CSV |

### Verified SEEALand figures

Cross-checked against the workbook, so the Phase 1 fixture has known-good targets:

| Quantity | Value |
|---|---|
| **Gross Ecosystem Product** | **$83,125** — and total supply equals total use, so the account balances |
| Forest asset value, opening → closing | $905,065.38 → $788,699.84 |
| Forest change in NPV | **−$116,365.55** |
| Total ecosystem asset value, opening | $3,572,206.88 |
| Largest single asset | Lake, $1,078,320.76 |

## Distilled reference

| File | What |
|---|---|
| `seea-ea-reference.md` | The controlled vocabularies and table structures the app must conform to — five accounts, spatial units, GET biomes, the ECT, the full ES reference list, reference-condition methods, and the SEEALand figures. The source for `system-prompt.md` and the app's versioned lookup tables |

## Retrieval notes

`seea.un.org` sits behind CloudFront and **returns 403 to `curl`**. Fetch with a tool that presents a
normal browser user-agent. Spreadsheets and PDFs both come down fine that way; extract locally with
`openpyxl` / `pypdf` rather than expecting a fetcher to parse them.

## Still outstanding

The UNSD supplemental tables (4, 5, 13–18, 25, 28) are maintained as **living documents** at
[seea.un.org](https://seea.un.org/content/supplemental-materials-and-tables-guidelines-biophysical-modelling)
and may be newer than the 2022 print versions extracted here — worth re-checking before finalising the
condition-variable selection ([#6](https://github.com/SchmidtDSE/unseea/issues/6)). Tracked in
[#1](https://github.com/SchmidtDSE/unseea/issues/1).
