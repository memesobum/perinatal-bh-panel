# Limitations

*Plain-language summary: what this panel cannot tell you. Read before using or citing any number. Each item is specific so a reader can judge how much it matters for their use.*

1. **Need is measured with stand-ins, not perinatal data.** No open source reports depression or substance use among pregnant and postpartum women for every county. The panel uses adult (all sexes, 18+) depression prevalence from CDC PLACES, which is a model-based small-area estimate, together with social vulnerability. These rank counties sensibly but do not measure perinatal depression, anxiety, or substance use directly. `births_x_depression` is a scale indicator, not a case count.

2. **The facility measure covers substance use treatment only.** FindTreatment.gov records the "Pregnant/postpartum women" program only for substance use listings. Mental health facilities that serve perinatal women are not identifiable from open data, so perinatal mental health capacity rests on clinician counts.

3. **Facility services are self-reported.** Listings reflect what facilities report to SAMHSA's annual survey and the directory at the access date (November 4, 2026). A listed program may have closed, have a waitlist, or serve few women. Facilities that do not participate in the survey are missing.

4. **Clinician counts measure registrations, not available care.** NPPES shows clinicians who registered to bill, at their primary practice address. It does not show whether they are practicing, accept Medicaid, take new patients, see pregnant patients, work full-time, or practice at more than one site. Telehealth across county lines is invisible. Counts agree well with AHRF's AMA physician counts (correlation 0.93 for obstetric, 0.89 for psychiatric on log scale) but run higher because they include nurse practitioners and midwives.

5. **County lines are not care boundaries.** Women often travel to a neighboring county for care. A county with no listing may be close to services across the line; a county with services may serve a much larger region. Travel distance is planned for a later version (NEXT_STEPS.md).

6. **Small counties are unstable.** 97 counties have fewer than 20 births a year. In these, one clinician or one listing moves the per-birth ratio and the gap score by a lot. Use `flag_small_births` and do not rank these counties against each other without care.

7. **Gap scores are relative.** Percentile ranks say where a county stands against other counties. A county with a negative gap is not necessarily well served; it is better served than most U.S. counties on these measures.

8. **Data years differ.** Births 2021 to 2023 (NCHS) or mid-2023 to mid-2024 (Census); women 15 to 44 in 2024; PLACES from BRFSS 2023 (2022 for Kentucky and Pennsylvania); SVI 2022; RUCC 2023; facilities, health centers, and clinicians in November 2026. Each column records its year.

9. **Kentucky and Pennsylvania use an older PLACES release** (BRFSS 2022) because the 2025 release omits them. Loving County, Texas has no PLACES value.

10. **Births for 48 counties** come from the Census estimate rather than NCHS: Connecticut's 9 planning regions (AHRF's NCHS figures use the old counties) and 39 very small counties where NCHS suppresses the figure.

11. **Geography mapping errors are possible.** About 0.3% of listings (85) and 0.8% of clinicians could not be placed in a county, and 58 health center sites have no address in HRSA's file. Some FindTreatment.gov coordinates point to a same-named town in another state; 10 such listings were caught by a state check and re-placed by ZIP (an 11th, Hartford, VT, could not be placed). ZIP codes that span counties are assigned to the county with most of the ZIP's land.

12. **Home visiting, certified community behavioral health clinics, and women's set-aside programs** were part of the author's Nevada mapping but have no open national county-level list suitable for this version.

13. **Territories are excluded** in v0.1.

14. **Listings are not places, and sites are not buildings.** `tx_listings_all` counts directory listings; one address often carries both a mental health and a substance use listing (26,557 placed listings sit at 18,908 addresses; `tx_locations_all` counts addresses). Health center capacity counts HRSA sites; 11,769 sites sit at 11,219 distinct addresses (for example a medical and a dental site in one building; `hc_locations` counts addresses). For pregnant/postpartum programs the effect is small: 4,585 placed listings sit at 4,516 addresses (`ppw_sud_locations`). Some shared addresses are separate programs in one office building; a few look like the same program listed twice under slightly different names. The county yes/no flag `no_ppw_sud_facility` is unaffected.
