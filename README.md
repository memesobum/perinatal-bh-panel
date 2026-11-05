# U.S. County Perinatal Behavioral Health Need and Capacity Panel

**Status:** Released v0.1.0 (verified by the author 2026-11-04) | **Repository:** https://github.com/memesobum/perinatal-bh-panel | **Maintainer:** Munachimso A. Emesobum, ORCID [0009-0002-7506-2153](https://orcid.org/0009-0002-7506-2153) | **License:** data and documents CC BY 4.0, code MIT

**In plain terms:** One free table with a row for every U.S. county. It shows how much mental health and substance use need pregnant and new mothers are likely to have, next to the treatment that is actually there for them. Rural and frontier counties are flagged. State and local agencies can use it to see where need runs ahead of services.

New here? Read [docs/START_HERE.md](docs/START_HERE.md) first. Unfamiliar terms are in [docs/GLOSSARY.md](docs/GLOSSARY.md).

## Why

CDC's analysis of 2020 maternal mortality review committee data from 38 states attributed 115 of the 511 pregnancy-related deaths with an identified underlying cause to mental health conditions. Agencies deciding where to add perinatal screening, referral, and treatment need county-level evidence of where need exceeds services. No open national table of this kind existed. This panel builds one from open federal sources only, scaling up the author's county mapping of Nevada's 17 counties for the Larson Institute.

## What is here

Three releases, each with its own DOI, sharing the county key `fips` (Census Vintage 2024 geography; 3,144 counties in the 50 states and DC):

| Release | File(s) | Contents |
|---|---|---|
| 1. Need measures | `data/processed/need_county.csv` | births, women 15 to 44, adult depression and mental distress (CDC PLACES), Social Vulnerability Index, rural and frontier flags, data years, small-number flags |
| 2. Capacity inventory | `capacity_county.csv`, `capacity_facilities.csv`, `capacity_hc_sites.csv`, `capacity_clinicians_by_zip.csv` | geocoded treatment listings with service flags, health center sites, obstetric and behavioral clinicians by NUCC taxonomy |
| 3. Gap scores | `gap_county.csv`, `panel_county.csv`, `report/figures/` | need and capacity percentile scores, gap score, national and in-state ranks, high-need/low-capacity flag |

```
code/            numbered scripts in run order (config.py holds every measurement decision)
data/raw/        PROVENANCE.txt (raw files are re-downloaded by code/01_fetch.py)
data/processed/  outputs, qa_report.txt
docs/            START_HERE, GLOSSARY, CODEBOOK, CODING_RULES, LIMITATIONS, VERIFY_CHECKLIST, NEXT_STEPS, PUBLISH_GUIDE, TALK_TRACK
report/          stats.json (every number quoted anywhere), figures/
tools/           provenance logger, publish gate, GitHub and Zenodo upload scripts
```

## Run it

```
pip install -r requirements.txt
bash run_all.sh
```

About 15 to 25 minutes, most of it downloading the 1 GB NPPES file. Read `data/processed/qa_report.txt` first. Federal listings change monthly, so a later run will differ slightly in facility and clinician counts; `data/raw/PROVENANCE.txt` records the fingerprint of every file used for this release.

## Sources

| Source | Vintage | Terms | Accessed |
|---|---|---|---|
| [Area Health Resources Files (HRSA)](https://data.hrsa.gov/data/download?data=AHRF) | 2024-2025 county CSV | U.S. public domain | 2026-11-04 |
| [Census Population Estimates, county characteristics and totals](https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/) | Vintage 2024 | U.S. public domain | 2026-11-04 |
| [CDC PLACES county data](https://data.cdc.gov/d/swc5-untb) (2025 release; [2024 release](https://data.cdc.gov/d/fu4u-a9bh) for KY and PA) | BRFSS 2023 (2022) | U.S. public domain | 2026-11-04 |
| [CDC/ATSDR Social Vulnerability Index](https://svi.cdc.gov/) | 2022 | U.S. public domain | 2026-11-04 |
| [USDA ERS Rural-Urban Continuum Codes](https://www.ers.usda.gov/data-products/rural-urban-continuum-codes) | 2023 | U.S. public domain | 2026-11-04 |
| [SAMHSA FindTreatment.gov locator API](https://findtreatment.gov/assets/FindTreatment-Developer-Guide.pdf) | live directory | U.S. public domain | 2026-11-04 |
| [HRSA Health Center Service Delivery and Look-Alike Sites](https://data.hrsa.gov/data/download) | live file | U.S. public domain | 2026-11-04 |
| [CMS NPPES downloadable file V.2](https://download.cms.gov/nppes/NPI_Files.html) | November 2026 | U.S. public domain | 2026-11-04 |
| [The NUCC Health Care Provider Taxonomy](https://www.nucc.org/index.php/code-sets-mainmenu-41/provider-taxonomy-mainmenu-40/csv-mainmenu-57) | v26.1 | free use with attribution | 2026-11-04 |
| [Census Gazetteer, cartographic boundaries, ZCTA-county relationship file](https://www.census.gov/geographies/reference-files.html) | 2024 / 2020 | U.S. public domain | 2026-11-04 |

## Headline numbers (from `report/stats.json`)

Of 3,144 counties, 1,793 (57.0%) have no substance use treatment listing for pregnant or postpartum women. That is 35.1% of metro, 65.5% of rural, and 86.6% of frontier counties, holding 12.7% of U.S. births. 107 counties combine top-quarter need with bottom-quarter capacity: 72 rural, 12 frontier, and 23 metro.

## Limitations

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) before using or citing anything here. In short: need uses adult depression and social vulnerability as stand-ins; the pregnant/postpartum facility flag exists only for substance use listings; clinician counts are registrations, not verified available care; small counties are unstable.

## Citation and authorship

See `CITATION.cff`. DOIs: added here as each Zenodo record is published. Munachimso A. Emesobum made every measurement decision and checked results against his Nevada county maps. Claude (Anthropic) assisted with code and data handling.
