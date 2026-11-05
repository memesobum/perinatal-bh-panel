"""config.py: every measurement decision in one place.

Plain-language summary: this file holds the choices that shape the panel, such
as which clinicians count, what "frontier" means, and how the gap score is built.
Each choice is marked DECISION and listed in docs/VERIFY_CHECKLIST.md Part 4.
Mr. Emesobum rules on each one. Changing a value here and re-running
code/03_build_need.py through code/08_package.py (or bash run_all.sh) rebuilds everything.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
REPORT = os.path.join(ROOT, "report")

VERSION = "0.1.0"
# Draft stamping. v0.1.0 was verified by the author on 2026-11-04, so stamps are off.
# For a future version, set this back to True (or run with PANEL_DRAFT=1) until it is verified again.
DRAFT = os.environ.get("PANEL_DRAFT") == "1"

# County universe: Census PEP Vintage 2024, 50 states + DC (3,144 county-equivalents,
# Connecticut as 9 planning regions). Puerto Rico and territories are out of scope for v0.1.
EXCLUDE_STATE_FIPS = {"72"}

# DECISION 1: births source.
# "nchs_then_census": NCHS 3-year average 2021-2023 (AHRF births_3yr_avg_23); Census PEP
# births July 2023-June 2024 (AHRF births_july_1_june_30_24) where NCHS is missing.
BIRTHS_RULE = "nchs_then_census"

# Small-number rule: a county value resting on fewer than this many events is flagged.
# 20 follows the NCHS convention that rates on fewer than 20 events are unreliable.
SMALL_N = 20

# DECISION 2: rural and frontier.
RURAL_RUCC = {4, 5, 6, 7, 8, 9}        # nonmetro
FRONTIER_DENSITY = 6.0                  # persons per square mile of land; below this = frontier

# DECISION 3: clinician taxonomy groups (NUCC v26.1 codes). A clinician is counted once,
# in the group of their primary taxonomy, at their primary practice-location ZIP.
TAXONOMY_GROUPS = {
    "obstetric": {
        "207V00000X": "Obstetrics & Gynecology",
        "207VX0000X": "OB/GYN, Obstetrics",
        "207VM0101X": "OB/GYN, Maternal & Fetal Medicine",
        "367A00000X": "Advanced Practice Midwife (includes CNM)",
        "176B00000X": "Midwife",
        "363LX0001X": "Nurse Practitioner, Obstetrics & Gynecology",
        "363LW0102X": "Nurse Practitioner, Women's Health",
        "363LP1700X": "Nurse Practitioner, Perinatal",
        "364SW0102X": "Clinical Nurse Specialist, Women's Health",
        "364SP1700X": "Clinical Nurse Specialist, Perinatal",
    },
    "bh_prescriber": {
        "2084P0800X": "Psychiatry",
        "2084P0802X": "Addiction Psychiatry",
        "2084P0015X": "Psychosomatic Medicine (consultation-liaison)",
        "2084A0401X": "Psychiatry & Neurology, Addiction Medicine",
        "207QA0401X": "Family Medicine, Addiction Medicine",
        "207RA0401X": "Internal Medicine, Addiction Medicine",
        "207LA0401X": "Anesthesiology, Addiction Medicine",
        "2083A0300X": "Preventive Medicine, Addiction Medicine",
        "363LP0808X": "Nurse Practitioner, Psychiatric/Mental Health",
        "364SP0808X": "Clinical Nurse Specialist, Psychiatric/Mental Health",
        "364SP0809X": "Clinical Nurse Specialist, Psychiatric/Mental Health, Adult",
        "364SP0810X": "Clinical Nurse Specialist, Psychiatric/Mental Health, Child & Family",
        "364SP0812X": "Clinical Nurse Specialist, Psychiatric/Mental Health, Community",
    },
    "bh_therapist": {
        "103T00000X": "Psychologist",
        "103TA0400X": "Psychologist, Addiction",
        "103TB0200X": "Psychologist, Cognitive & Behavioral",
        "103TC0700X": "Psychologist, Clinical",
        "103TC1900X": "Psychologist, Counseling",
        "103TF0000X": "Psychologist, Family",
        "103TH0004X": "Psychologist, Health",
        "103TH0100X": "Psychologist, Health Service",
        "103TP0016X": "Psychologist, Prescribing (Medical)",
        "103TP0814X": "Psychologist, Psychoanalysis",
        "103TP2700X": "Psychologist, Psychotherapy",
        "103TP2701X": "Psychologist, Group Psychotherapy",
        "103TW0100X": "Psychologist, Women",
        "1041C0700X": "Social Worker, Clinical",
        "101Y00000X": "Counselor",
        "101YA0400X": "Counselor, Addiction (Substance Use Disorder)",
        "101YM0800X": "Counselor, Mental Health",
        "101YP2500X": "Counselor, Professional",
        "106H00000X": "Marriage & Family Therapist",
    },
    "family_medicine": {
        "207Q00000X": "Family Medicine (reported separately; not in obstetric total)",
    },
}

# FindTreatment.gov service coding rules (field f2 code, value text in f3).
FT_PPW = ("SG", "Pregnant/postpartum women")          # primary capacity flag
FT_WOMEN = ("SG", "Adult women")
FT_CHILDCARE = ("AS", "Child care for clients' children")
FT_RES_CHILD_BEDS = ("AS", "Residential beds for clients' children")

# DECISION 4: gap score.
# Need score = mean percentile rank of NEED_COMPONENTS. Capacity score = mean percentile rank
# of CAPACITY_COMPONENTS (all per 1,000 births). Gap = need score - capacity score.
NEED_COMPONENTS = ["depression_crude_pct", "svi_overall"]
# DECISION 4b: counties with fewer births than this get no need, capacity, or gap score and are
# left out of the percentile ranks (they stay in the table with ranked = 0). 0 = rank every county.
MIN_BIRTHS_TO_RANK = 0
CAPACITY_COMPONENTS = [
    "ppw_sud_facilities_per_1k_births",
    "bh_clinicians_per_1k_births",
    "ob_clinicians_per_1k_births",
    "hc_sites_per_1k_births",
]

STATE_ABBR = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC",
    "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT",
    "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY",
}
