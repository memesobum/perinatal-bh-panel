# Coding rules: what counts as capacity

*Plain-language summary: this file says exactly which facilities and clinicians are counted, and why. If you disagree with a rule, change it in `code/config.py` (or `code/04_build_capacity.py` for health centers) and re-run. Every rule here is a measurement decision Mr. Emesobum signs off on.*

## 1. Treatment facilities (SAMHSA FindTreatment.gov)

**How the listings were obtained.** FindTreatment.gov has no single bulk file. The public locator API (Developer Guide v1.12, August 17, 2026) returns all listings in a state when called with `limitType=0` and the state's API ID (Appendix B of the guide; these IDs are not FIPS codes). The service type parameter `sType` was left out, so substance use, mental health, and opioid treatment program listings are all returned. 51 queries (50 states + DC), page size 2,000, accessed November 4, 2026. Every query returned its full reported count.

**De-duplication.** Listings with the same name, street, ZIP, and listing type are counted once (27,506 rows returned, 26,642 unique).

**Placing listings in counties.** Coordinates inside a 2024 Census county boundary (cartographic boundary file, 1:500,000). Listings with no coordinates are placed by ZIP code using the rule in section 4. **State check:** if the coordinates fall in a county of a different state than the listing's own state (a same-named town elsewhere, such as Arlington, OR placed in Texas), the listing is re-placed by ZIP, and only if the ZIP is in the listed state. 10 listings were corrected this way, 2 of them pregnant/postpartum programs. 85 listings (mostly P.O. box ZIP codes, plus Hartford, VT) could not be placed and are listed in the QA report.

**Pregnant/postpartum flag (`serves_ppw`).** The listing's "Special Programs/Groups Offered" field (code `SG`) contains the exact value "Pregnant/postpartum women". This is what the facility reported to SAMHSA's annual survey; it is not verified by this project.

**Important:** only substance use (SA) listings carry the pregnant/postpartum field. None of the 12,637 mental health listings and none of the 1,958 opioid treatment program listings have it. The facility measure is therefore **substance use treatment for pregnant and postpartum women**, named `ppw_sud_facilities`. Federally certified opioid treatment programs must give pregnant women priority admission, but they are counted separately (`tx_listings_otp`) and not as pregnant/postpartum programs.

**Supporting flags** (not in the gap score): "Adult women" (SG), "Child care for clients' children" (AS), "Residential beds for clients' children" (AS), Medicaid accepted (PAY), medications for opioid use disorder offered (OM).

## 2. Health center sites (HRSA)

From HRSA's "Health Center Service Delivery and Look-Alike Sites" file (downloaded November 4, 2026), a site is counted when all are true:

- Site status is Active.
- Site type is "Service Delivery Site" or "Administrative/Service Delivery Site" (administrative-only offices are not counted).
- Location type is "Permanent" (seasonal sites and mobile vans are not counted).
- Setting is not School, Correctional Facility, or Transitional Care in Carceral Setting (these do not serve the general population of pregnant women).

19,528 sites in the file; 11,992 meet the rules. County comes from HRSA's own county code; one site with a blank code (Oakland, CA) is placed by ZIP. Of the 11,992: 11,769 are in the 50 states and DC; 165 are in Puerto Rico and the territories; 58 have no address in HRSA's file (state shown as "XX") and cannot be placed. The 11,769 sites sit at 11,219 distinct addresses, because one building often holds several sites of the same health center (for example medical and dental). The gap score counts sites; `hc_locations` counts addresses.

## 3. Clinicians (CMS NPPES, November 2026 file)

- Individuals only (entity type 1). Organizations are not counted.
- Active: no deactivation date, or reactivated after deactivation.
- **Each clinician counted once**, in the group of their **primary taxonomy** (the code marked primary; if none is marked, the first listed code).
- **Location** = primary business practice address, U.S. only. Secondary practice locations are not counted.
- An NPI shows that a clinician registered to bill. It does not prove they are currently practicing, licensed in that state, seeing pregnant patients, or full-time.

| Group | NUCC codes (v26.1) |
|---|---|
| **Obstetric** (`ob_clinicians`) | 207V00000X OB/GYN; 207VX0000X Obstetrics; 207VM0101X Maternal & Fetal Medicine; 367A00000X Advanced Practice Midwife; 176B00000X Midwife; 363LX0001X NP Obstetrics & Gynecology; 363LW0102X NP Women's Health; 363LP1700X NP Perinatal; 364SW0102X CNS Women's Health; 364SP1700X CNS Perinatal |
| **Behavioral prescriber** (`bh_prescribers`) | 2084P0800X Psychiatry; 2084P0802X Addiction Psychiatry; 2084P0015X Psychosomatic Medicine; 2084A0401X, 207QA0401X, 207RA0401X, 207LA0401X, 2083A0300X Addiction Medicine (all boards); 363LP0808X Psychiatric/Mental Health NP; 364SP0808X, 364SP0809X, 364SP0810X, 364SP0812X Psychiatric/Mental Health CNS |
| **Behavioral therapist** (`bh_therapists`) | Psychologists: 103T00000X, 103TA0400X, 103TB0200X, 103TC0700X, 103TC1900X, 103TF0000X, 103TH0004X, 103TH0100X, 103TP0016X, 103TP0814X, 103TP2700X, 103TP2701X, 103TW0100X; 1041C0700X Clinical Social Worker; Counselors 101Y00000X, 101YA0400X, 101YM0800X, 101YP2500X; 106H00000X Marriage & Family Therapist |
| **Family medicine** (reported only) | 207Q00000X Family Medicine |

**Left out on purpose:** gynecology-only and gynecologic subspecialties (207VG0400X, 207VX0201X, 207VE0102X, 207VF0040X, and others), lay midwives (175M00000X), child and adolescent psychiatry, school psychologists and counselors, pastoral counselors, social workers without the clinical specialty, and registered nurses. Family physicians are reported but not added to obstetric capacity, because NPPES cannot show which of them deliver babies.

## 4. ZIP code to county

- Each ZIP is treated as its ZIP Code Tabulation Area (ZCTA) and assigned to the county holding the largest share of its land area (Census 2020 ZCTA-to-county relationship file).
- **Connecticut:** that file still uses the old 8 counties. Connecticut ZCTAs are placed in the 2022 planning regions by their 2024 Gazetteer interior point.
- ZIPs that are not ZCTAs (many P.O. box and single-building ZIPs) are left unmatched: 12,439 clinicians (0.8%), listed by count in the QA report.

## 5. Small numbers

- `flag_small_births`: births below 20 (NCHS convention for unreliable rates). Per-birth capacity ratios in these counties swing widely; 2 clinicians in a county with 18 births looks like very high capacity.
- `flag_small_count_ppw_sud`: 1 or 2 pregnant/postpartum listings.
- Counties with 0 births have no per-birth ratios and no capacity score (Kalawao County, HI).
