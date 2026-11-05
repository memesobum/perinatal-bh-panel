#!/usr/bin/env python3
"""01_fetch.py: download every raw input, and log where each came from.

Plain-language summary: this script downloads the public files the panel is
built from and writes one line per file to data/raw/PROVENANCE.txt (file name,
size, fingerprint, web address, date). You do not need to open it. Run it once;
re-running skips files already downloaded unless you pass --refresh.

Sources (all free and public; see README for vintages and terms):
  AHRF 2024-2025 county CSV (HRSA)              births, OB/GYN and psychiatrist counts
  Census PEP Vintage 2024 county age-sex file   women aged 15 to 44
  Census PEP Vintage 2024 components of change  births July 2023 to June 2024
  CDC PLACES county data (Socrata swc5-untb)    adult depression prevalence
  CDC/ATSDR SVI 2022 county file                social vulnerability
  USDA ERS Rural-Urban Continuum Codes 2023     rural classification
  Census 2024 Gazetteer counties                land area (frontier density)
  Census 2020 ZCTA-to-county relationship file  assign clinician ZIPs to counties
  HRSA health center service delivery sites     FQHC and look-alike sites
  FindTreatment.gov locator API (SAMHSA)        treatment facility listings, by state
  NPPES monthly V.2 file (CMS)                  clinicians by taxonomy code
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PROV = os.path.join(RAW, "PROVENANCE.txt")
TOOLS = os.path.join(ROOT, "tools", "provenance.py")
UA = {"User-Agent": "perinatal-bh-panel/0.1 (open research data build)"}

STATIC = {
    "AHRF_2024-2025_CSV.zip": ("https://data.hrsa.gov/DataDownload/AHRF/AHRF_2024-2025_CSV.zip",
                               "Linked from https://data.hrsa.gov/data/download?data=AHRF (County AHRF 2024-2025, CSV)"),
    "AHRF_USER_TECH_2024-2025.zip": ("https://data.hrsa.gov/DataDownload/AHRF/AHRF_USER_TECH_2024-2025.zip",
                                     "AHRF 2024-2025 technical documentation; births variables on doc rows births_3yr_avg_23, births_july_1_june_30_24"),
    "cc-est2024-agesex-all.csv": ("https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/asrh/cc-est2024-agesex-all.csv",
                                  "Census PEP Vintage 2024 county characteristics, age and sex"),
    "co-est2024-alldata.csv": ("https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv",
                               "Census PEP Vintage 2024 county totals and components of change"),
    "SVI_2022_US_county.csv": ("https://svi.cdc.gov/Documents/Data/2022/csv/states_counties/SVI_2022_US_county.csv",
                               "CDC/ATSDR SVI 2022, United States, county level"),
    "Ruralurbancontinuumcodes2023.csv": ("https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/53251/Ruralurbancontinuumcodes2023.csv",
                                         "USDA ERS RUCC 2023, linked from https://www.ers.usda.gov/data-products/rural-urban-continuum-codes"),
    "2024_Gaz_counties_national.zip": ("https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_counties_national.zip",
                                       "Census 2024 Gazetteer, counties"),
    "2024_Gaz_zcta_national.zip": ("https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_zcta_national.zip",
                                   "Census 2024 Gazetteer, ZCTAs; interior points used to place Connecticut ZIPs in planning regions"),
    "tab20_zcta520_county20_natl.txt": ("https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt",
                                        "Census 2020 ZCTA to county relationship file"),
    "cb_2024_us_county_500k.zip": ("https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip",
                                   "Census 2024 cartographic boundary file, counties, 1:500,000; used to place facilities in counties and draw maps"),
    "nucc_taxonomy_261.csv": ("https://www.nucc.org/images/stories/CSV/nucc_taxonomy_261.csv",
                              "NUCC Health Care Provider Taxonomy code set v26.1, linked from nucc.org CSV page"),
    "Health_Center_Service_Delivery_and_LookAlike_Sites.csv": (
        "https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv",
        "HRSA Data Warehouse, Health Center Service Delivery and Look-Alike Sites"),
}

# CDC PLACES county data. Dataset id from https://data.cdc.gov (PLACES: Local Data for Better Health, County Data).
PLACES_ID = "swc5-untb"          # 2025 release (BRFSS 2023)
PLACES_FALLBACK_ID = "fu4u-a9bh"  # 2024 release (BRFSS 2022)
PLACES_URL = (f"https://data.cdc.gov/resource/{PLACES_ID}.csv?"
              "$select=year,stateabbr,locationname,locationid,measureid,datavaluetypeid,data_value,"
              "low_confidence_limit,high_confidence_limit,totalpopulation,totalpop18plus"
              "&$where=measureid='DEPRESSION' OR measureid='MHLTH'&$limit=50000")

# FindTreatment.gov API state IDs (Developer Guide v1.12, Aug 17 2026, Appendix B). Not FIPS codes.
FT_STATE_IDS = {
    "AL": 19, "AK": 20, "AZ": 21, "AR": 22, "CA": 23, "CO": 24, "CT": 25, "DE": 26, "DC": 27, "FL": 28,
    "GA": 29, "HI": 30, "ID": 31, "IL": 32, "IN": 33, "IA": 34, "KS": 35, "KY": 36, "LA": 37, "ME": 1,
    "MD": 18, "MA": 3, "MI": 2, "MN": 38, "MS": 39, "MO": 40, "MT": 4, "NE": 41, "NV": 12, "NH": 42,
    "NJ": 13, "NM": 43, "NY": 5, "NC": 6, "ND": 44, "OH": 7, "OK": 45, "OR": 46, "PA": 8, "RI": 9,
    "SC": 47, "SD": 48, "TN": 10, "TX": 11, "UT": 14, "VT": 49, "VA": 50, "WA": 15, "WV": 51, "WI": 16,
    "WY": 52,
}
FT_BASE = "https://findtreatment.gov/locator/exportsAsJson/v2"


def log(path, url, note=""):
    subprocess.run([sys.executable, TOOLS, path, url, "--log", PROV, "--note", note], check=True,
                   stdout=subprocess.DEVNULL)


def get(url, dest, note, refresh, stream=True):
    if os.path.exists(dest) and not refresh:
        print(f"  have {os.path.basename(dest)}")
        return
    print(f"  fetching {os.path.basename(dest)}")
    for attempt in range(5):
        try:
            with requests.get(url, headers=UA, stream=stream, timeout=600) as r:
                r.raise_for_status()
                tmp = dest + ".part"
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            os.replace(tmp, dest)
            break
        except Exception as e:  # network hiccups: retry with backoff
            print(f"    retry {attempt + 1}: {e}")
            time.sleep(5 * (attempt + 1))
    else:
        raise SystemExit(f"FAILED {url}")
    log(dest, url, note)


def fetch_findtreatment(refresh):
    """All listings, state by state, from the public locator API (limitType=0 = state search).

    sType is omitted so substance use, mental health, and opioid treatment program
    listings are all returned (Developer Guide, Appendix A). pageSize max is 2000.
    """
    dest = os.path.join(RAW, "findtreatment_all_states.json")
    if os.path.exists(dest) and not refresh:
        print("  have findtreatment_all_states.json")
        return
    out = {}
    for st, sid in FT_STATE_IDS.items():
        rows, page = [], 1
        while True:
            q = {"sAddr": '"-98.5,39.8"', "limitType": 0, "limitValue": sid, "pageSize": 2000, "page": page, "sort": 0}
            url = FT_BASE + "?" + urllib.parse.urlencode(q)
            for attempt in range(6):
                try:
                    r = requests.get(url, headers=UA, timeout=180)
                    r.raise_for_status()
                    d = r.json()
                    break
                except Exception as e:
                    print(f"    {st} p{page} retry {attempt + 1}: {e}")
                    time.sleep(5 * (attempt + 1))
            else:
                raise SystemExit(f"FAILED FindTreatment {st}")
            rows.extend(d.get("rows") or [])
            if page >= (d.get("totalPages") or 1):
                break
            page += 1
        out[st] = {"recordCount": d.get("recordCount"), "rows": rows}
        print(f"  FindTreatment {st}: {len(rows)} (reported {d.get('recordCount')})")
        time.sleep(0.5)
    with open(dest, "w") as f:
        json.dump(out, f)
    log(dest, FT_BASE + "?limitType=0&limitValue=<state id>&pageSize=2000 (51 state queries, sType omitted)",
        "Public FindTreatment.gov locator API per Developer Guide v1.12 (2026-08-17); state IDs from its Appendix B")


def fetch_nppes(refresh):
    """Current monthly NPPES V.2 file. CMS rotates the file name monthly, so it is read from the index page."""
    idx = "https://download.cms.gov/nppes/NPI_Files.html"
    html = requests.get(idx, headers=UA, timeout=120).text
    m = re.search(r"href='\./(NPPES_Data_Dissemination_[A-Za-z]+_\d{4}_V2\.zip)'", html)
    if not m:
        raise SystemExit("Could not find the monthly V.2 NPPES file on the index page")
    name = m.group(1)
    existing = [f for f in os.listdir(RAW) if f.startswith("NPPES_Data_Dissemination_") and f.endswith("_V2.zip")]
    if existing and not refresh:
        print(f"  have {existing[0]} (index currently lists {name})")
        return
    get("https://download.cms.gov/nppes/" + name, os.path.join(RAW, name),
        f"Monthly V.2 file name discovered from {idx} on the access date", refresh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download everything")
    ap.add_argument("--skip-nppes", action="store_true", help="skip the 1 GB NPPES file")
    a = ap.parse_args()
    os.makedirs(RAW, exist_ok=True)
    for fn, (url, note) in STATIC.items():
        get(url, os.path.join(RAW, fn), note, a.refresh)
    get(PLACES_URL, os.path.join(RAW, "places_county_depression_mhlth.csv"),
        f"CDC PLACES county data, Socrata dataset {PLACES_ID}, measures DEPRESSION and MHLTH", a.refresh)
    # The 2025 release has no Kentucky or Pennsylvania counties. The 2024 release (BRFSS 2022) fills them.
    get(PLACES_URL.replace(PLACES_ID, PLACES_FALLBACK_ID), os.path.join(RAW, "places2024_county_depression_mhlth.csv"),
        f"CDC PLACES county data 2024 release, Socrata dataset {PLACES_FALLBACK_ID}; used only for states absent from {PLACES_ID}",
        a.refresh)
    fetch_findtreatment(a.refresh)
    if not a.skip_nppes:
        fetch_nppes(a.refresh)
    print("Done. See data/raw/PROVENANCE.txt")


if __name__ == "__main__":
    main()
