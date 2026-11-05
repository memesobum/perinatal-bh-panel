# Codebook

*Plain-language summary: every column in every table, what it means, where it comes from, and how it was computed. One row in each county table is one U.S. county (or county-equivalent). Open this when a column name is unclear.*

**Key used in every county table:** `fips` is the 5-digit county code (2-digit state + 3-digit county), as used by the Census Bureau in Vintage 2024 population estimates. Connecticut appears as its 9 planning regions (09110 to 09190), not its 8 former counties.

**Universe:** 3,144 counties and county-equivalents in the 50 states and the District of Columbia. Puerto Rico and the territories are not included in v0.1.

**Missing values** are blank cells. A blank is never a zero.

---

## Release 1: `need_county.csv` (need measures)

| Column | Definition | Source and year | How computed |
|---|---|---|---|
| fips | County code | Census PEP V2024 | STATE + COUNTY |
| state_fips | State code | Census PEP V2024 | |
| state | State postal abbreviation | | from state_fips |
| county_name | County name | Census PEP V2024 | CTYNAME |
| pop_total_2024 | Total resident population, July 1, 2024 | Census PEP V2024 `co-est2024-alldata` | POPESTIMATE2024 |
| women_15_44 | Female residents aged 15 to 44, July 1, 2024 | Census PEP V2024 `cc-est2024-agesex-all` | AGE1544_FEM, YEAR = 6 |
| women_15_44_year | Reference date of women_15_44 | | "2024-07-01" |
| births | Annual births used in the panel | see births_source | DECISION 1: NCHS 3-year average where available, otherwise Census PEP |
| births_source | Which births value was used | | text |
| births_years | Years covered by `births` | | "2021-2023" (NCHS) or "2023-07 to 2024-06" (Census) |
| births_nchs_3yr_avg | Average annual births to county residents, 2021 to 2023 | AHRF 2024-2025, variable `births_3yr_avg_23` (NCHS Natality File) | as published; blank where NCHS suppressed it or for Connecticut planning regions |
| births_census_2024 | Births, July 1, 2023 to June 30, 2024 | Census PEP V2024 `co-est2024-alldata`, BIRTHS2024 (same values as AHRF `births_july_1_june_30_24`) | as published |
| general_fertility_rate | Births per 1,000 women aged 15 to 44 | derived | 1000 x births / women_15_44 |
| depression_crude_pct | Percent of adults 18+ ever told they have a depressive disorder | CDC PLACES county data (model-based, from BRFSS) | measure DEPRESSION, crude prevalence |
| depression_crude_lcl, depression_crude_ucl | 95% confidence limits for depression_crude_pct | CDC PLACES | |
| depression_ageadj_pct | Age-adjusted depression prevalence | CDC PLACES | measure DEPRESSION, age-adjusted |
| mental_distress_crude_pct | Percent of adults with 14+ days of poor mental health in past 30 days | CDC PLACES | measure MHLTH, crude |
| mental_distress_ageadj_pct | Age-adjusted version of the above | CDC PLACES | |
| places_release | PLACES release used | | "PLACES 2025" (Socrata swc5-untb, BRFSS 2023); "PLACES 2024" (fu4u-a9bh, BRFSS 2022) only for Kentucky and Pennsylvania, which the 2025 release omits |
| places_brfss_year | BRFSS survey year behind the PLACES estimate | CDC PLACES | |
| births_x_depression | Births weighted by adult depression prevalence | derived | births x depression_crude_pct / 100. **A proxy for scale of need, not an estimate of perinatal depression cases.** |
| svi_overall | Overall Social Vulnerability Index percentile (0 = least, 1 = most vulnerable), ranked nationally | CDC/ATSDR SVI 2022, county, U.S. file | RPL_THEMES |
| svi_socioeconomic | SVI theme 1 percentile | CDC/ATSDR SVI 2022 | RPL_THEME1 |
| svi_household | SVI theme 2 percentile (household characteristics) | CDC/ATSDR SVI 2022 | RPL_THEME2 |
| svi_minority_language | SVI theme 3 percentile (racial and ethnic minority status) | CDC/ATSDR SVI 2022 | RPL_THEME3 |
| svi_housing_transport | SVI theme 4 percentile (housing type and transportation) | CDC/ATSDR SVI 2022 | RPL_THEME4 |
| svi_year | SVI vintage | | "2022 (ACS 2018-2022)" |
| rucc_2023 | Rural-Urban Continuum Code, 1 (largest metro) to 9 (most rural) | USDA ERS RUCC 2023 | as published |
| rucc_year | RUCC vintage | | "2023" |
| land_sqmi | Land area, square miles | Census 2024 Gazetteer, counties | ALAND_SQMI |
| pop_density_2024 | Persons per square mile of land | derived | pop_total_2024 / land_sqmi |
| rural | 1 = nonmetro (RUCC 4 to 9), 0 = metro | derived | DECISION 2 |
| frontier | 1 = fewer than 6 persons per square mile | derived | DECISION 2 |
| rurality_class | "frontier", "rural", or "metro" | derived | frontier takes precedence; 22 frontier counties are metro by RUCC (e.g. Matanuska-Susitna Borough, AK, RUCC 2) |
| flag_small_births | 1 = births below 20 | derived | rates and per-birth ratios are unstable (NCHS convention) |
| flag_births_census_fallback | 1 = births came from Census, not NCHS | derived | |
| flag_places_prior_release | 1 = depression from PLACES 2024 release | derived | Kentucky and Pennsylvania |
| flag_missing_depression | 1 = no PLACES value | derived | Loving County, TX only |
| flag_missing_svi | 1 = no SVI value | derived | |

---

## Release 2: capacity inventory

### `capacity_facilities.csv` (one row per FindTreatment.gov listing)

| Column | Definition |
|---|---|
| facility_id | Stable 12-character ID: first 12 hex digits of SHA-1 of lowercase name + street + ZIP + listing type. Used to remove exact duplicates. |
| location_id | 12-character ID of lowercase street + ZIP. Listings sharing it are at one address. |
| query_state | State whose API query returned the listing |
| name, name2, street, city, state, zip, phone, website | As listed in FindTreatment.gov |
| latitude, longitude | As listed (WGS84). Blank for about 7% of listings. |
| facility_type | "SA" substance use, "MH" mental health, "OTP" opioid treatment program, as listed |
| serves_ppw | 1 = "Special Programs/Groups Offered" (code SG) includes "Pregnant/postpartum women". **Only substance use listings carry this field.** |
| serves_adult_women | 1 = SG includes "Adult women" |
| childcare_for_clients | 1 = "Ancillary Services" (AS) includes "Child care for clients' children" |
| residential_beds_for_children | 1 = AS includes "Residential beds for clients' children" |
| accepts_medicaid | 1 = "Payment/Insurance/Funding Accepted" (PAY) includes "Medicaid" |
| offers_moud | 1 = listing has an "Opioid Medications used in Treatment" (OM) entry |
| service_setting | Text of the "Service Setting" (SET) field |
| services_listed | 0 = listing returned with no service detail (all OTP listings) |
| fips | County the listing is placed in |
| geo_method | "point_in_polygon" (coordinates inside a 2024 county boundary); "nearest_within_2km" (coordinates just outside every boundary, e.g. on a coastline; placed in the nearest county within 2 km; none occurred in v0.1); "zip_to_county" (no coordinates; ZIP rule in CODING_RULES.md); "zip_to_county_after_state_mismatch" (coordinates fell in a county of another state, so placed by ZIP instead); or "unassigned" |

### `capacity_hc_sites.csv` (one row per counted HRSA health center site)

| Column | Definition |
|---|---|
| bphc_site_id | HRSA BPHC assigned site number |
| site_name, health_center_name, health_center_type | As published (FQHC or FQHC Look-Alike) |
| address, city, state, zip | Site address |
| fips | County code as published by HRSA |
| longitude, latitude | HRSA geocode |
| setting | Location setting description |
| operating_hours_per_week | As published |
| geo_method | "hrsa_county_code" (HRSA's own county code), "zip_to_county" (code missing; placed by ZIP), "unplaced_no_address_in_hrsa_file" (HRSA publishes no address), or "unassigned" |
| location_id | 12-character ID of normalized address + ZIP; sites sharing it are in one building |

### `capacity_clinicians_by_zip.csv` (no names or NPIs)

| Column | Definition |
|---|---|
| zip5 | Primary practice-location ZIP (5 digits) |
| fips | County the ZIP is assigned to (blank if unmatched) |
| group | obstetric, bh_prescriber, bh_therapist, or family_medicine (see CODING_RULES.md) |
| clinicians | Number of active individual NPIs |

### `capacity_county.csv`

| Column | Definition |
|---|---|
| fips, state, county_name | Keys |
| tx_listings_all | All FindTreatment.gov listings in the county |
| tx_locations_all | Distinct addresses among those listings (one address often has both a mental health and a substance use listing) |
| tx_listings_mh, tx_listings_sa, tx_listings_otp | Listings by type |
| ppw_sud_facilities | Listings with serves_ppw = 1 (substance use treatment programs for pregnant/postpartum women) |
| ppw_sud_locations | Distinct addresses among those listings |
| women_program_facilities | Listings with serves_adult_women = 1 |
| childcare_facilities, res_child_beds_facilities | Listings offering child care / residential beds for clients' children |
| ppw_sud_facilities_medicaid | ppw_sud listings that accept Medicaid |
| ppw_sud_facilities_moud | ppw_sud listings that offer medication for opioid use disorder |
| hc_sites | Counted HRSA health center sites |
| hc_locations | Distinct addresses among those sites |
| ob_clinicians | Individual NPIs, primary taxonomy in the obstetric group |
| bh_prescribers | Individual NPIs, primary taxonomy in the behavioral prescriber group |
| bh_therapists | Individual NPIs, primary taxonomy in the behavioral therapist group |
| bh_clinicians | bh_prescribers + bh_therapists |
| family_medicine_physicians | Individual NPIs with primary taxonomy 207Q00000X (reported separately) |
| *_per_1k_births | Count x 1,000 / births (births from need_county.csv). Blank where births = 0. |
| mh_listings_per_1k_births | Mental health listings per 1,000 births (not in the default gap score) |
| no_ppw_sud_facility | 1 = ppw_sud_facilities is 0 |
| no_bh_prescriber, no_ob_clinician | 1 = count is 0 |
| flag_small_count_ppw_sud | 1 = 1 or 2 ppw_sud listings (one opening or closing changes the county's status) |
| findtreatment_access_date, nppes_file, hrsa_sites_file_date | Data dates for the capacity sources |

---

## Release 3: `gap_county.csv`

| Column | Definition |
|---|---|
| fips, state, county_name, rurality_class, rural, frontier, births, flag_small_births | Carried from need table |
| ranked | 1 = county is scored and ranked; 0 = left unranked because births are below MIN_BIRTHS_TO_RANK in code/config.py (0 in this build, so every county with births is ranked) |
| pr_depression_crude_pct, pr_svi_overall | National percentile rank (0 to 100) of each need component; higher = more need |
| need_score | Mean of the need percentile ranks |
| need_components_n | Number of need components available (2 except Loving County, TX) |
| pr_ppw_sud_facilities_per_1k_births, pr_bh_clinicians_per_1k_births, pr_ob_clinicians_per_1k_births, pr_hc_sites_per_1k_births | National percentile rank of each capacity component; higher = more capacity |
| capacity_score | Mean of the capacity percentile ranks |
| capacity_components_n | Number of capacity components available |
| gap_score | need_score minus capacity_score, -100 to +100. **Positive = need ranks above capacity.** |
| gap_rank_national | 1 = largest gap in the U.S. |
| gap_rank_in_state | 1 = largest gap in the state |
| high_need_low_capacity | 1 = need_score in the top quarter AND capacity_score in the bottom quarter nationally |
| no_ppw_sud_facility, no_bh_prescriber, no_ob_clinician | Carried from capacity table |

Percentile rank = 100 x (rank among ranked counties with a value / number of such counties), ties averaged. Ranks are relative: a county's score says where it stands against other counties, not whether services are adequate in absolute terms.

`panel_county.csv` joins all three county tables in one file for convenience.
