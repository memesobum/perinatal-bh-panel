#!/usr/bin/env python3
"""06_qa.py: quality checks, Nevada spot checks, and the stats files.

Plain-language summary: counts rows at each step, checks ranges, compares our
clinician counts against an independent source (AHRF's AMA counts), lists the
Nevada values for hand checking, and picks extreme and random counties to
check. Each release gets only its own checks and numbers, so publishing
Release 1 does not reveal Release 3 results early:
  data/processed/qa_release1_need.txt      + report/stats_release1_need.json
  data/processed/qa_release2_capacity.txt  + report/stats_release2_capacity.json
  data/processed/qa_report.txt (all three) + report/stats.json (all three; Release 3 and the repository)
Every number any document quotes comes from a stats file.
"""

import io
import json
import os
import sys
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import DRAFT, MIN_BIRTHS_TO_RANK, PROC, RAW, REPORT, VERSION  # noqa: E402

SEED = 20261104
NV_NEED = ["county_name", "rurality_class", "rucc_2023", "pop_density_2024", "births", "women_15_44",
           "depression_crude_pct", "svi_overall"]
NV_CAP = ["county_name", "tx_listings_all", "tx_locations_all", "ppw_sud_facilities", "hc_sites", "ob_clinicians",
          "bh_prescribers", "bh_therapists", "family_medicine_physicians"]
NV_GAP = ["county_name", "births", "need_score", "capacity_score", "gap_score", "gap_rank_in_state"]


def ahrf_md():
    with zipfile.ZipFile(os.path.join(RAW, "AHRF_2024-2025_CSV.zip")) as z:
        n = [x for x in z.namelist() if x.endswith("AHRF2025hp.csv")][0]
        cols = ["fips_st_cnty", "md_nf_obgyn_gen_all_pc_23", "md_nf_obgyn_subsp_all_pc_23", "md_nf_psych_all_pc_23"]
        h = pd.read_csv(io.BytesIO(z.read(n)), dtype=str, encoding="latin1", usecols=cols)
    out = pd.DataFrame({"fips": h.fips_st_cnty})
    out["ahrf_obgyn_pc_2023"] = pd.to_numeric(h.md_nf_obgyn_gen_all_pc_23, errors="coerce") + pd.to_numeric(
        h.md_nf_obgyn_subsp_all_pc_23, errors="coerce")
    out["ahrf_psych_pc_2023"] = pd.to_numeric(h.md_nf_psych_all_pc_23, errors="coerce")
    return out


def header(title):
    return [f"QA REPORT  {title}  v{VERSION}" + ("  DRAFT (unverified)" if DRAFT else ""),
            "Plain-language summary: this file is the build's self-check. Each section says what was",
            "counted and whether it passed. The Nevada section is for comparing with your county maps.", ""]


def rng_check(d, c, lo, hi):
    v = d[c].dropna()
    bad = int(((v < lo) | (v > hi)).sum())
    return (f"  {c}: min {v.min():.2f} median {v.median():.2f} max {v.max():.2f}; outside [{lo},{hi}]: {bad}  "
            f"{'PASS' if bad == 0 else 'CHECK'}")


def need_section(d):
    L = ["1. COUNTY UNIVERSE AND JOINS (need table)",
         f"  counties (Census PEP V2024, 50 states + DC): {len(d)}  [expect 3144]  {'PASS' if len(d) == 3144 else 'CHECK'}",
         f"  duplicate FIPS: {d.fips.duplicated().sum()}  {'PASS' if d.fips.duplicated().sum() == 0 else 'FAIL'}"]
    for c in ["women_15_44", "births", "depression_crude_pct", "svi_overall", "rucc_2023", "land_sqmi"]:
        miss = d[d[c].isna()]
        L.append(f"  missing {c}: {len(miss)}  {list(miss.fips + ' ' + miss.county_name)[:5]}")
    ct = int(((d.flag_births_census_fallback == 1) & (d.state == "CT")).sum())
    oth = int(((d.flag_births_census_fallback == 1) & (d.state != "CT")).sum())
    L += [f"  births source: NCHS 3-yr avg {int((d.flag_births_census_fallback == 0).sum())}; Census fallback "
          f"{ct + oth} ({ct} Connecticut planning regions + {oth} counties NCHS suppressed)",
          f"  PLACES prior release (2024, BRFSS 2022) used for: {int(d.flag_places_prior_release.sum())} counties (KY, PA)",
          "", "2. RANGE AND SANITY CHECKS (need table)"]
    for c, lo, hi in [("depression_crude_pct", 5, 40), ("svi_overall", 0, 1), ("general_fertility_rate", 10, 150),
                      ("rucc_2023", 1, 9)]:
        L.append(rng_check(d, c, lo, hi))
    for _, r in d[(d.general_fertility_rate < 10) | (d.general_fertility_rate > 150)].iterrows():
        L.append(f"    GFR outlier: {r.fips} {r.county_name}, {r.state}: births {r.births}, women 15-44 {r.women_15_44}")
    L += [f"  births sum: {d.births.sum():,.0f}  (U.S. registers about 3.6 million births a year)",
          f"  women 15-44 sum: {d.women_15_44.sum():,.0f}", "",
          "3. NEVADA NEED VALUES", d[d.state == "NV"].sort_values("county_name")[NV_NEED].to_string(index=False), ""]
    st = {"version": VERSION, "build_date": "2026-11-04", "n_counties": int(len(d)), "n_states": int(d.state.nunique()),
          "n_metro": int((d.rurality_class == "metro").sum()), "n_rural": int((d.rurality_class == "rural").sum()),
          "n_frontier": int((d.rurality_class == "frontier").sum()), "births_total": int(round(d.births.sum())),
          "n_births_census_fallback": ct + oth, "n_births_fallback_ct": ct, "n_births_fallback_suppressed": oth,
          "n_places_prior_release": int(d.flag_places_prior_release.sum()),
          "n_small_births": int(d.flag_small_births.sum())}
    return L, st


def capacity_section(d, capstats, nppes_stats, fac):
    gm = capstats["ft_geo_method"]
    hg = capstats["hc_geo_method"]
    L = ["4. FINDTREATMENT.GOV LISTINGS",
         f"  rows returned by 51 state queries: {capstats['ft_rows_raw']:,}",
         f"  unique listings after de-duplication (name+street+ZIP+type): {capstats['ft_unique']:,}",
         f"  unique street addresses (locations) among placed listings: {capstats['ft_locations']:,}"
         "  (one place often holds both a mental health and a substance use listing)",
         f"  placed in a county: {capstats['ft_assigned']:,} ({100 * capstats['ft_assigned'] / capstats['ft_unique']:.1f}%)"
         f"  methods: {gm}",
         f"  coordinates pointed to a county in another state, re-placed by ZIP: {capstats['ft_state_mismatch_fixed']}",
         f"  listing types: {capstats['ft_type_counts']}",
         f"  listings coded 'Pregnant/postpartum women': {capstats['ft_ppw_total']:,}"]
    un = fac[fac.geo_method == "unassigned"]
    L.append(f"  unassigned listings ({len(un)}), mostly P.O. box ZIPs; first 10:")
    for _, r in un.head(10).iterrows():
        L.append(f"    {r['name']} | {r.street} | {r.city}, {r.state} {r.zip}")
    L += ["", "5. HRSA HEALTH CENTER SITES",
          f"  active sites in file: {capstats['hc_rows_raw']:,}; counted under coding rules: {capstats['hc_kept']:,}",
          f"  placement: {hg}",
          f"  in the 50 states + DC: {capstats['hc_in_panel']:,} sites at {capstats['hc_in_panel_locations']:,} distinct addresses",
          f"  in Puerto Rico and territories: {capstats['hc_in_territories']} with a territory county code, plus "
          f"{hg.get('unassigned', 0)} in the Marshall Islands and Palau with none",
          f"  no address published by HRSA (state 'XX'), cannot be placed: {hg.get('unplaced_no_address_in_hrsa_file', 0)}",
          "", "6. NPPES CLINICIANS",
          f"  NPPES records read: {int(nppes_stats['rows_read']):,}; individual (type 1): {int(nppes_stats['type1']):,}",
          f"  kept by primary taxonomy: {int(nppes_stats['kept']):,}; U.S. practice address: {capstats['nppes_us']:,}",
          f"  ZIP-to-county: {capstats['nppes_zip_match']}",
          f"  in territories (outside panel): {capstats['nppes_outside_universe']:,}",
          f"  by group: {capstats['nppes_group_counts']}"]
    a = d.merge(ahrf_md(), on="fips", how="left")
    ob = a[["ob_clinicians", "ahrf_obgyn_pc_2023"]].dropna()
    ps = a[["bh_prescribers", "ahrf_psych_pc_2023"]].dropna()
    r_ob = np.corrcoef(np.log1p(ob.iloc[:, 0]), np.log1p(ob.iloc[:, 1]))[0, 1]
    r_ps = np.corrcoef(np.log1p(ps.iloc[:, 0]), np.log1p(ps.iloc[:, 1]))[0, 1]
    L += ["  External check vs AHRF (AMA Physician Masterfile 2023, patient-care MDs):",
          f"    obstetric clinicians vs AHRF OB/GYN: correlation of log counts r = {r_ob:.3f} (n={len(ob)})",
          f"    BH prescribers vs AHRF psychiatrists: r = {r_ps:.3f} (n={len(ps)})",
          "    Note: NPPES group includes midwives and NPs; AHRF counts MDs only, so NPPES totals run higher.", "",
          "7. NEVADA CAPACITY VALUES", d[d.state == "NV"].sort_values("county_name")[NV_CAP].to_string(index=False), ""]
    nvf = fac[(fac.state == "NV") & (fac.serves_ppw == 1)].sort_values(["fips", "name"])
    L.append(f"  Nevada listings coded Pregnant/postpartum women ({len(nvf)}):")
    names = d.set_index("fips").county_name
    for _, r in nvf.iterrows():
        L.append(f"    {names.get(r.fips, '?'):18s} {r.facility_type:3s} {r['name']} | {r.street}, {r.city}")
    L.append("")
    by_r = d.groupby("rurality_class")
    nv = d[d.state == "NV"]
    st = {"ft_unique": capstats["ft_unique"], "ft_locations": capstats["ft_locations"],
          "ft_ppw_total": capstats["ft_ppw_total"],
          "ft_assigned_pct": round(100 * capstats["ft_assigned"] / capstats["ft_unique"], 1),
          "ft_unassigned": int(gm.get("unassigned", 0)), "ft_state_mismatch_fixed": capstats["ft_state_mismatch_fixed"],
          "hc_sites_counted": int(d.hc_sites.sum()), "hc_locations_counted": int(d.hc_locations.sum()),
          "hc_unplaced_no_address": int(hg.get("unplaced_no_address_in_hrsa_file", 0)),
          "clinicians_counted": int((d.ob_clinicians + d.bh_clinicians + d.family_medicine_physicians).sum()),
          "ob_clinicians_total": int(d.ob_clinicians.sum()), "bh_prescribers_total": int(d.bh_prescribers.sum()),
          "bh_therapists_total": int(d.bh_therapists.sum()),
          "family_medicine_total": int(d.family_medicine_physicians.sum()),
          "n_no_ppw_sud_facility": int(d.no_ppw_sud_facility.sum()),
          "pct_no_ppw_sud_facility": round(100 * d.no_ppw_sud_facility.mean(), 1),
          "pct_births_in_no_ppw_counties": round(
              100 * d.loc[d.no_ppw_sud_facility == 1, "births"].sum() / d.births.sum(), 1),
          "pct_no_ppw_by_class": {k: round(100 * v, 1) for k, v in by_r.no_ppw_sud_facility.mean().items()},
          "n_no_bh_prescriber": int(d.no_bh_prescriber.sum()),
          "r_ob_vs_ahrf": round(float(r_ob), 3), "r_psych_vs_ahrf": round(float(r_ps), 3),
          "nv_ppw_listings": int(len(nvf)), "nv_counties_no_ppw": int(nv.no_ppw_sud_facility.sum())}
    return L, st


def gap_section(d):
    L = ["8. GAP SCORES", f"  minimum births to be ranked: {MIN_BIRTHS_TO_RANK} (0 = every county ranked); "
                          f"ranked counties: {int(d.ranked.sum())}"]
    for c, lo, hi in [("need_score", 0, 100), ("capacity_score", 0, 100), ("gap_score", -100, 100)]:
        L.append(rng_check(d, c, lo, hi))
    L += ["", "9. NEVADA GAP VALUES", d[d.state == "NV"].sort_values("county_name")[NV_GAP].to_string(index=False), ""]
    rng = np.random.default_rng(SEED)
    r_ = d[d.gap_score.notna()]
    sel = [("largest gap", r_.nlargest(5, "gap_score")), ("smallest gap", r_.nsmallest(5, "gap_score")),
           ("random", d.iloc[rng.choice(len(d), 5, replace=False)])]
    L.append(f"10. SPOT CHECKS (random seed {SEED})")
    for lab, s in sel:
        for _, r in s.iterrows():
            L.append(f"  {lab:12s} {r.fips} {r.county_name}, {r.state}: births {r.births:.0f}, ppw_sud {r.ppw_sud_facilities}, "
                     f"bh_clin {r.bh_clinicians}, ob {r.ob_clinicians}, hc {r.hc_sites}, need {r.need_score}, "
                     f"cap {r.capacity_score}, gap {r.gap_score}")
    L.append("")
    small = d[d.births < 20]
    big = d[d.births > 2000]
    hn = d[d.high_need_low_capacity == 1]
    st = {"min_births_to_rank": MIN_BIRTHS_TO_RANK, "n_ranked": int(d.ranked.sum()),
          "n_high_need_low_capacity": int(len(hn)),
          "high_need_low_capacity_by_class": {k: int(v) for k, v in hn.rurality_class.value_counts().items()},
          "high_need_low_capacity_nonmetro_rucc": int((hn.rural == 1).sum()),
          "median_gap_by_class": {k: round(float(v), 1) for k, v in d.groupby("rurality_class").gap_score.median().items()},
          "median_capacity_small_births": round(float(small.capacity_score.median()), 1) if small.capacity_score.notna().any() else None,
          "median_capacity_births_over_2000": round(float(big.capacity_score.median()), 1)}
    return L, st


def write(path_txt, lines, path_json, stats):
    with open(path_txt, "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(path_json, "w") as f:
        json.dump(stats, f, indent=2)


def main():
    os.makedirs(REPORT, exist_ok=True)
    d = pd.read_csv(os.path.join(PROC, "panel_county.csv"), dtype={"fips": str, "state_fips": str})
    capstats = json.load(open(os.path.join(PROC, "capacity_build_stats.json")))
    nppes_stats = dict(l.strip().split("=", 1) for l in open(os.path.join(PROC, "nppes_extract_stats.txt")))
    fac = pd.read_csv(os.path.join(PROC, "capacity_facilities.csv"), dtype={"fips": str})

    nL, nS = need_section(d)
    cL, cS = capacity_section(d, capstats, nppes_stats, fac)
    gL, gS = gap_section(d)
    T = "U.S. County Perinatal Behavioral Health Need and Capacity Panel"
    write(os.path.join(PROC, "qa_release1_need.txt"), header(T + ", Release 1 (need)") + nL,
          os.path.join(REPORT, "stats_release1_need.json"), nS)
    write(os.path.join(PROC, "qa_release2_capacity.txt"), header(T + ", Release 2 (capacity)") + cL,
          os.path.join(REPORT, "stats_release2_capacity.json"), {**{k: nS[k] for k in ("version", "build_date", "n_counties")}, **cS})
    allL = header(T) + nL + cL + gL
    write(os.path.join(PROC, "qa_report.txt"), allL, os.path.join(REPORT, "stats.json"), {**nS, **cS, **gS})
    print("\n".join(allL))


if __name__ == "__main__":
    main()
