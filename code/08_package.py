#!/usr/bin/env python3
"""08_package.py: assemble the three Zenodo release packages.

Plain-language summary: copies the right files for each of the three releases
into dist/, zips each one, and writes the Zenodo metadata file each upload
needs (title, author, description, license, keywords). Author details come
from AUTHORS.json. While the package is a draft, every release README carries
a DRAFT banner and every Zenodo title says so; the publish gate blocks upload
until those are gone.
"""

import json
import os
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(__file__))
from config import DRAFT, PROC, RAW, REPORT, ROOT, VERSION  # noqa: E402

DIST = os.path.join(ROOT, "dist")
A = json.load(open(os.path.join(ROOT, "AUTHORS.json")))
ST = json.load(open(os.path.join(REPORT, "stats.json")))
BASE_TITLE = "U.S. County Perinatal Behavioral Health Need and Capacity Panel"
# Files keep their repository paths inside each zip, so run_all.sh works from an unzipped release.
COMMON_DOCS = ["docs/LIMITATIONS.md", "docs/CODEBOOK.md", "docs/CODING_RULES.md", "docs/GLOSSARY.md", "docs/NEXT_STEPS.md", "LICENSE-DATA.md",
               "LICENSE", "CITATION.cff", "AUTHORS.json", "requirements.txt", "run_all.sh", "data/raw/PROVENANCE.txt",
               "tools/provenance.py", "tools/publish_gate.py"]

RELEASES = {
    "release1_need": {
        "title": f"{BASE_TITLE}: Release 1, County Need Measures (v{VERSION})",
        "files": ["data/processed/need_county.csv"],
        "extra_docs": ["data/processed/qa_release1_need.txt", "report/stats_release1_need.json"],
        "summary": (
            f"County-level need measures for perinatal mental health and substance use for all {ST['n_counties']:,} "
            "U.S. counties and county-equivalents (50 states and DC): births (NCHS 3-year average 2021-2023, Census "
            "fallback), women aged 15-44 (Census 2024), adult depression and frequent mental distress prevalence (CDC "
            "PLACES), CDC/ATSDR Social Vulnerability Index 2022, USDA Rural-Urban Continuum Codes 2023, land area and "
            "population density, and rural and frontier flags. Every measure carries its data year; small-number and "
            "source-substitution flags are included. With codebook and provenance log."),
    },
    "release2_capacity": {
        "title": f"{BASE_TITLE}: Release 2, Capacity Inventory (v{VERSION})",
        "files": ["data/processed/capacity_county.csv", "data/processed/capacity_facilities.csv",
                  "data/processed/capacity_hc_sites.csv", "data/processed/capacity_clinicians_by_zip.csv"],
        "extra_docs": ["data/processed/qa_release2_capacity.txt",
                       "report/stats_release2_capacity.json"],
        "summary": (
            f"Geocoded inventory of perinatal behavioral health capacity by U.S. county: {ST['ft_unique']:,} SAMHSA "
            f"FindTreatment.gov treatment listings with service flags ({ST['ft_ppw_total']:,} substance use listings "
            f"with a pregnant/postpartum women program), {ST['hc_sites_counted']:,} HRSA health center sites, and "
            f"{ST['clinicians_counted']:,} obstetric, behavioral health, and family medicine clinicians from NPPES "
            "identified by NUCC taxonomy code, aggregated to counties. Includes the service-type coding rules."),
    },
    "release3_gap": {
        "title": f"{BASE_TITLE}: Release 3, Need-to-Capacity Gap Scores (v{VERSION})",
        "files": ["data/processed/gap_county.csv", "data/processed/panel_county.csv",
                  "report/figures/fig1_gap_map_national.png", "report/figures/fig2_no_ppw_by_rurality.png",
                  "report/figures/fig3_nevada_gap.png"],
        "extra_docs": ["data/processed/qa_report.txt", "report/stats.json"],
        "summary": (
            "County need-to-capacity gap scores for perinatal behavioral health for every U.S. county, with rural "
            f"({ST['n_rural']:,}) and frontier ({ST['n_frontier']:,}) classification. Need and capacity are each "
            "scored as mean national percentile ranks; the gap is need minus capacity. Flags mark counties with no "
            f"substance use treatment listing for pregnant or postpartum women ({ST['n_no_ppw_sud_facility']:,} counties, "
            f"{ST['pct_births_in_no_ppw_counties']}% of births) and counties with high need and low capacity "
            f"({ST['n_high_need_low_capacity']:,})."),
    },
}

KEYWORDS = ["perinatal mental health", "maternal mental health", "postpartum", "substance use treatment",
            "county health data", "rural health", "frontier", "health workforce", "open data"]


def readme(key, r):
    banner = ("**DRAFT, NOT VERIFIED. Do not cite or reuse until the author's verification is complete.**\n\n"
              if DRAFT else "")
    au = A["authors"][0]
    return f"""# {r['title']}

{banner}**Author:** {au['name']} ({au['affiliation']}), ORCID https://orcid.org/{au['orcid']}, {au['email']}

## What this is

{r['summary']}

Part of a three-release panel. Release 1 holds need measures, Release 2 the capacity inventory, Release 3 the gap
scores. All three share the county key `fips` (Census Vintage 2024 geography).

## Files

{chr(10).join('- `' + f + '`' for f in r['files'])}
- `docs/CODEBOOK.md` column definitions; `docs/LIMITATIONS.md` read before use; `data/raw/PROVENANCE.txt` every
  source file with URL, date, size, and SHA-256; `{r['extra_docs'][-2]}` quality checks; `{r['extra_docs'][-1]}`
  headline numbers.
- `code/` and `tools/` the full pipeline. To rebuild from the public sources: `pip install -r requirements.txt`
  then `bash run_all.sh` (15 to 25 minutes; federal listings change monthly, so counts will shift slightly).

## Sources

AHRF 2024-2025 (HRSA); Census Population Estimates Vintage 2024 and 2024 Gazetteer and cartographic boundaries;
CDC PLACES 2025 county release (2024 release for KY and PA); CDC/ATSDR SVI 2022; USDA ERS RUCC 2023; SAMHSA
FindTreatment.gov locator API (accessed 2026-11-04); HRSA Health Center Service Delivery and Look-Alike Sites
(2026-11-04); CMS NPPES V.2 monthly file (November 2026); NUCC taxonomy v26.1; Census 2020 ZCTA-county
relationship file.

## License

Data and documents: CC BY 4.0. Code: MIT. {A['ai_assistance']}
"""


def zenodo_meta(key, r):
    creators = [{"name": f"{a['family']}, {a['given']}", "orcid": a["orcid"], "affiliation": a["affiliation"]}
                for a in A["authors"] + A.get("collaborators", [])]
    return {
        "upload_type": "dataset",
        "title": ("DRAFT " if DRAFT else "") + r["title"],
        "creators": creators,
        "description": f"<p>{r['summary']}</p><p>Built only from open U.S. federal sources. See LIMITATIONS.md "
                       "before use. Data CC BY 4.0; code MIT.</p>",
        "license": "cc-by-4.0",
        "keywords": KEYWORDS,
        "version": VERSION,
        "access_right": "open",
        "related_identifiers": [{"identifier": "https://github.com/memesobum/perinatal-bh-panel",
                                 "relation": "isSupplementTo", "scheme": "url"}],
        "language": "eng",
    }


def main():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    for key, r in RELEASES.items():
        d = os.path.join(DIST, key)
        os.makedirs(d)
        for f in r["files"] + COMMON_DOCS + r["extra_docs"]:
            os.makedirs(os.path.dirname(os.path.join(d, f)), exist_ok=True)
            shutil.copy2(os.path.join(ROOT, f), os.path.join(d, f))
        shutil.copytree(os.path.join(ROOT, "code"), os.path.join(d, "code"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        with open(os.path.join(d, "README.md"), "w") as fh:
            fh.write(readme(key, r))
        zpath = os.path.join(DIST, f"{key}_v{VERSION}.zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for dp, _, fns in os.walk(d):
                for fn in fns:
                    p = os.path.join(dp, fn)
                    z.write(p, os.path.join(key, os.path.relpath(p, d)))
        with open(os.path.join(DIST, f"{key}_zenodo_metadata.json"), "w") as fh:
            json.dump(zenodo_meta(key, r), fh, indent=2)
        print(f"{zpath}  {os.path.getsize(zpath) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
