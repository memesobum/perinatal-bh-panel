# Your verification checklist

**Record for v0.1.0:** On 2026-11-04 Mr. Emesobum stated that he had verified the package and approved publishing. Part 4 decisions were kept as built: births-based ratios, every county ranked (`MIN_BIRTHS_TO_RANK = 0`), health centers counted as sites, pregnant/postpartum programs counted as listings. Reuse this checklist for each future version.

*Plain-language summary: before anything goes public under your name, you check it. Everything below is filled in with this project's real files, rows, and numbers. Total time: about 2 hours, best done in two sittings. Tick each box and write the date. Open `.csv` files in Excel or Google Sheets. Row numbers count the header as row 1.*

*The publish gate checks the mechanical items automatically. These are yours.*

## Part 1: Make sure the results can be rebuilt (20 to 30 min)

Pick one:
- [ ] **Option A, run it yourself.** In a terminal inside the project folder, paste:
  `pip install -r requirements.txt` then `bash run_all.sh`.
  It takes 15 to 25 minutes, mostly downloading the 1 GB clinician file. The last line should read
  `Done. Read data/processed/qa_report.txt first.`
- [ ] **Option B, ask Claude.** In a new chat with Opus 5.5 or Fable 5, upload the project and say: "Re-run this pipeline from scratch and give me the headline numbers from report/stats.json." Compare with these:
  3,144 counties; 26,642 treatment listings; 4,600 pregnant/postpartum listings; 11,769 health center sites; 1,793 counties with no pregnant/postpartum listing.
  Facility and clinician numbers will move a little if the federal files have been updated since November 4, 2026. That is expected. Large changes are not.

Then:
- [ ] Section 1 of `data/processed/qa_report.txt` says PASS for county count and duplicates.
- [ ] Every number in `README.md` and the Zenodo descriptions matches `report/stats.json`.

## Part 2: Check the sources (15 min)

- [ ] Each source link in `README.md` still opens and is free.
- [ ] Every source is a U.S. federal public-domain product, or the NUCC code list, which is free to use with attribution. No source blocks reuse. Confirm you agree.
- [ ] The two items your brief marked for verification are settled the way you want:
  - Births in AHRF 2024-2025 = `births_3yr_avg_23` (NCHS, 2021 to 2023) and `births_july_1_june_30_24` (Census). Open `data/raw/AHRF_USER_TECH_2024-2025.zip`, then the Technical Documentation spreadsheet, and search "births_3yr".
  - FindTreatment.gov bulk route = the public locator API, state by state. See https://findtreatment.gov/assets/FindTreatment-Developer-Guide.pdf, Appendix A and B.
- [ ] The CDC figure in the README and talk track matches the CDC page "Pregnancy-Related Deaths: Data From Maternal Mortality Review Committees in 38 U.S. States, 2020", Table 4: mental health conditions 115 of the 511 deaths with a known underlying cause.

## Part 3: Check rows by hand (45 to 60 min)

**Nevada counties you know** (file `data/processed/panel_county.csv`, or `need_county.csv` for the row numbers given). Compare with your Larson Institute maps first, then with the public source.
- [ ] Washoe (row 1765): 6 pregnant/postpartum substance use listings; 12 health center sites. Check the listings by name in the QA report, Section 6, against your map. ___
- [ ] Elko (row 1754): 1 pregnant/postpartum listing (Vitality Integrated Programs Elko); 4 health center sites; frontier. Check sites at https://findahealthcenter.hrsa.gov (search "Elko, NV"). ___
- [ ] Clark (row 1752): 23 pregnant/postpartum listings; births 24,629. At https://findtreatment.gov search "Las Vegas, NV" and spot-check three listing names from the QA report. ___
- [ ] Esmeralda (row 1755): births 2 (Census, because NCHS suppresses it); no listings, no clinicians. Does that match your map? ___
- [ ] Nye (row 1762): 2 listings, both in Pahrump; 3 health center sites; frontier. ___
- [ ] Your maps show OB/GYN providers. Pick one small county. At https://npiregistry.cms.hhs.gov search Taxonomy "Obstetrics & Gynecology", State NV, City (e.g. Elko). Compare with `ob_clinicians` (Elko: 7, which also includes midwives and women's health nurse practitioners). ___

**Extreme values** (most likely to hide an error)
- [ ] Mahnomen County, MN (row 1361): largest gap in the U.S., +72.8. Births 77, depression 26.6%, SVI 0.958, no listings, no health center site, no OB clinician. Check depression at https://data.cdc.gov/d/swc5-untb (filter LocationName = Mahnomen, Measure = Depression). ___
- [ ] Warren County, NY (row 1888): smallest gap, -69.8. 42 OB clinicians and 13 health center sites for 521 births. Check sites at findahealthcenter.hrsa.gov (Glens Falls, NY). ___
- [ ] Storey County, NV (row 1764): gap -64.8 resting on 18 births. Confirm you agree this is a small-number effect (see Part 4, decision 4). ___

**Random rows** (seed 20261104)
- [ ] Pleasants County, WV (row 3032): births 62, depression 30.7%, gap +34.2. ___
- [ ] Ford County, KS (row 920): births 581, 1 listing, 3 health center sites, gap -14.0. ___
- [ ] Emery County, UT (row 2788): RUCC 9, density 2.28, frontier, gap -17.9. Check RUCC at https://www.ers.usda.gov/data-products/rural-urban-continuum-codes. ___

## Part 4: Your decisions (15 min)

The build made these choices provisionally. Agree or change each one. They live in `code/config.py`.
- [ ] **1. Births source.** NCHS 3-year average, with Census where NCHS is missing (48 counties). Alternative: Census single-year everywhere, which is simpler but noisier for small counties. Your choice: ___
- [ ] **2. Rural and frontier.** Rural = RUCC 4 to 9; frontier = under 6 people per square mile. Result: 1,164 metro, 1,563 rural, 417 frontier. In Nevada this makes Churchill frontier, and Lyon and Storey metro. Keep, or use another rule your Nevada work used? Your choice: ___
- [ ] **3. Clinician groups.** As in `docs/CODING_RULES.md`. Family physicians reported separately, not added to obstetric capacity. Your choice: ___
- [ ] **4. Gap score.** Need = mean percentile of depression and SVI. Capacity = mean percentile of 4 per-birth ratios. Tiny counties are unstable in both directions. Most score *low* on capacity because they have no facility at all (median capacity score 21 for counties under 20 births, against 67 for counties over 2,000 births). A few jump high from one clinician (Storey, NV: gap -64.8 on 18 births). Options:
  - A. Keep as is and rely on the small-births flag.
  - B. Count capacity per 1,000 women aged 15 to 44 instead of per 1,000 births. *Tested: this does not help.* Gap scores correlate 0.994 with the current ones, and Storey only moves to -63.5.
  - C. Leave counties under 20 births unranked (97 counties). They stay in the table with their counts and flags, but get no scores and are left out of everyone else's percentiles. Set `MIN_BIRTHS_TO_RANK = 20` in `code/config.py`.
  Recommended: C. Your choice: ___
- [ ] **5. Mental health facilities.** Add mental health listings per 1,000 births as a fifth capacity component? It is already in the data as `mh_listings_per_1k_births`, though these listings say nothing about perinatal service. Recommended: no, keep as context. Your choice: ___
- [ ] **6. Health center sites.** Permanent, non-school, non-correctional service sites (11,769 counted). Option: count distinct addresses instead (11,219), so a medical and a dental site in one building count once. Recommended: addresses, since a pregnant woman experiences one building as one place of care. Your choice: ___
- [ ] **7. Treatment listings vs. places.** The gap score uses only pregnant/postpartum listings (4,585 placed, at 4,516 addresses). Count addresses (`ppw_sud_locations`) instead? It removes a few same-program duplicates but also merges separate programs sharing an office building. Recommended: keep listings; the difference is 1.5%. Your choice: ___

## Part 5: Before it goes public (20 to 30 min)

- [ ] The README summary and each Zenodo description are rewritten in your own words. Nothing remains you could not explain or defend. (Claude can do this with you line by line.)
- [ ] Your name, ORCID, affiliation, and email are correct in `AUTHORS.json` and `CITATION.cff`.
- [ ] You have read `docs/LIMITATIONS.md` and agree with it.
- [ ] Draft stamps removed (done for v0.1.0: the draft switch is off in `code/config.py`), then
  `python3 tools/publish_gate.py dist/release1_need --allow-draft-in code tools` (and release2, release3). The `code` and `tools` exceptions are there because the scripts contain the draft switch and the gate's own search patterns. Each must print "gate: clear".
- [ ] Evidence log row written on release day (template in `docs/PUBLISH_GUIDE.md`).

**When every box is ticked, reply to Claude in your own words that you have checked the package and approve publishing.**
