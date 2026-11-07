# Start Here: U.S. County Perinatal Behavioral Health Need and Capacity Panel

*Read this first. It explains your project in plain language. Words in bold are explained in [GLOSSARY.md](GLOSSARY.md).*

## What you are building

One free, public table with a row for every U.S. county. Each row shows how much mental health and substance use need pregnant and new mothers in that county are likely to have, next to how much treatment is actually there for them.

## Why it matters

Mental health conditions caused 115 of the 511 pregnancy-related deaths with a known cause in CDC's 2020 review of 38 states. That is more than one in five. State and county agencies have to decide where to add screening, referral, and treatment for pregnant and postpartum women. Today they have no open national table showing where need is high and services are thin.

In your Nevada work with the Larson Institute, you mapped this by hand for 17 counties. You also found that some county data could not be obtained through a state request. This project does the same thing for all 3,144 counties, using only public files anyone can download.

Think of it like a weather map, but each county shows two readings side by side: the storm (need) and the shelter (services).

## Where the information comes from

All sources are free and public. Nothing here needs special permission.

| Source | In plain terms | What one row looks like |
|---|---|---|
| Area Health Resources Files (AHRF) 2024-2025, HRSA | The federal government's yearly county fact book on health care | One county: births, number of OB/GYN doctors, psychiatrists |
| Census population estimates, Vintage 2024 | The official yearly count of people in each county by age and sex | One county: number of women aged 15 to 44 |
| CDC PLACES, 2025 release | CDC's estimate of how common depression is among adults in each county | One county: percent of adults ever told they have depression |
| CDC/ATSDR Social Vulnerability Index (SVI) 2022 | A score for how hard a county would be hit by a crisis, based on poverty, housing, transport and more | One county: a score from 0 (least vulnerable) to 1 (most) |
| FindTreatment.gov, SAMHSA | The federal directory of licensed mental health and addiction treatment places | One facility: name, address, map location, and the groups it serves, such as "Pregnant/postpartum women" |
| HRSA health center sites | The list of every federally funded community health center location | One clinic site: address, map location, county |
| NPPES, CMS | The national registry every billing clinician must join | One clinician: specialty code and practice ZIP code |
| USDA Rural-Urban Continuum Codes 2023 | The government's rural-to-urban scale for counties | One county: a code from 1 (big city) to 9 (most rural) |
| Census Gazetteer 2024 | Official land area of each county | One county: square miles of land (used to find frontier counties) |

## What you will have at the end

- [ ] **A public project page** on GitHub where anyone can see and reuse the work: https://github.com/memesobum/perinatal-bh-panel (once pushed)
- [ ] **Release 1, Need measures** (target February 2027): county need table, codebook, provenance log. Its own **DOI** on Zenodo.
- [ ] **Release 2, Capacity inventory** (target March 2027): every facility and clinician by county, with the rules for what counts. Its own DOI.
- [ ] **Release 3, Gap scores** (target April 2027): need compared with capacity in every county, with rural and frontier flags. Its own DOI.
- [ ] A short technical report and county maps, built from the same numbers.

All three are being built now. The dates are when they go public, after you check them.

## How it connects to your work

It scales your Nevada county mapping to the whole country, using only open data. It gives health agencies one shared evidence base for deciding where to put perinatal mental health services.

## What you need to do

| Your task | When | Time |
|---|---|---|
| Create GitHub and Zenodo accounts | Before publishing | 10 min |
| Answer five setup questions | Now | 10 min |
| Check the Nevada results against your own county maps | When the draft is ready | 1 to 2 hours |
| Approve publishing each release | After checking | 5 min each |

Everything else is built for you. You make every measurement decision. Claude writes the code and handles the data.

## The steps ahead

1. **Data collected.** Download every public source and record exactly where each came from.
2. **Tables built.** Combine sources into the need table, the capacity inventory, and the gap table.
3. **Quality checks and first maps.** Count, compare, flag anything odd, and check Nevada closely.
4. **Ready for your check.** Documentation, checklist, and publishing guide. You verify, then we publish.

*You are here: released. v0.1.0 is on GitHub and on Zenodo with DOI 10.5281/zenodo.24025395 (2026-11-07). Next: post the preprint.*
