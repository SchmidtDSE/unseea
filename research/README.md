# Source documents

Primary sources for the design, checked in so the analysis is reproducible and so the agent's reference
tables can be traced to a page. Both PDFs are freely redistributable UN publications.

| File | What | Retrieved |
|---|---|---|
| `seea_ea_white_cover_final.pdf` | **SEEA Ecosystem Accounting (2021), White Cover**, 393 pp — the standard, adopted by the UN Statistical Commission in March 2021 | 2026-07-30 from [seea.un.org](https://seea.un.org/sites/seea.un.org/files/documents/EA/seea_ea_white_cover_final.pdf) |
| `seea-ea-fulltext.txt` | Text extraction of the above, `===PAGE n===` delimited | derived |
| `unsd_guidelines_biophysical_modelling_2022.pdf` | **UNSD Guidelines on Biophysical Modelling for Ecosystem Accounting (2022)**, 221 pp — per-service model recommendations, the Tier framework, condition-indicator tables, global data-source annex | 2026-07-30 from [seea.un.org](https://seea.un.org/sites/default/files/publications/guidancebiomodelling_v36_30032022_web.pdf) |
| `unsd-biophysical-modelling-fulltext.txt` | Text extraction of the above | derived |
| `seea-ea-reference.md` | **Distilled reference** — the controlled vocabularies and table structures the app must conform to | hand-written from the extractions |

## Page numbering

The extractions use **PDF page numbers**, which run ahead of the printed page numbers the standards use in
their own cross-references (~22 pages of front matter in SEEA EA). When a section reference doesn't land,
that offset is usually why.

## Retrieval note

`seea.un.org` sits behind CloudFront and **returns 403 to `curl`**. Fetch with a tool that presents a
normal browser user-agent.

## Still to obtain

See [#1](https://github.com/SchmidtDSE/unseea/issues/1) — most importantly the **SEEALand complementary
spreadsheet**, which holds the cell-level condition workings and NPV-by-ET sheets that the printed annex
only summarises, and which blocks Phase 1.
