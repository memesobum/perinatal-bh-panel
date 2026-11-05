#!/usr/bin/env python3
"""03_build_need.py: build the county need table (Release 1).

Plain-language summary: makes data/processed/need_county.csv, one row per
U.S. county, with births, women aged 15 to 44, adult depression prevalence,
social vulnerability, and rural and frontier flags. Every measure has a
column saying which year its data covers, and small-number flags. Column
definitions are in docs/CODEBOOK.md.
"""

import io
import os
import sys
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import (BIRTHS_RULE, EXCLUDE_STATE_FIPS, FRONTIER_DENSITY, PROC, RAW,  # noqa: E402
                    RURAL_RUCC, SMALL_N, STATE_ABBR)


def num(s):
    return pd.to_numeric(s, errors="coerce")


def universe():
    c = pd.read_csv(os.path.join(RAW, "co-est2024-alldata.csv"), dtype=str, encoding="latin1")
    c = c[c.SUMLEV == "050"].copy()
    c["fips"] = c.STATE + c.COUNTY
    c = c[~c.STATE.isin(EXCLUDE_STATE_FIPS)]
    out = pd.DataFrame({
        "fips": c.fips, "state_fips": c.STATE, "state": c.STATE.map(STATE_ABBR),
        "county_name": c.CTYNAME, "pop_total_2024": num(c.POPESTIMATE2024),
        "births_census_2024": num(c.BIRTHS2024),
    })
    return out.reset_index(drop=True)


def women_15_44():
    a = pd.read_csv(os.path.join(RAW, "cc-est2024-agesex-all.csv"), dtype=str, encoding="latin1")
    a = a[a.YEAR == "6"]  # YEAR 6 = July 1, 2024 estimate (Census file layout)
    return pd.DataFrame({"fips": a.STATE + a.COUNTY, "women_15_44": num(a.AGE1544_FEM)})


def ahrf_births():
    with zipfile.ZipFile(os.path.join(RAW, "AHRF_2024-2025_CSV.zip")) as z:
        n = [x for x in z.namelist() if x.endswith("AHRF2025pop.csv")][0]
        p = pd.read_csv(io.BytesIO(z.read(n)), dtype=str, encoding="latin1",
                        usecols=["fips_st_cnty", "births_3yr_avg_23", "births_july_1_june_30_24"])
    return pd.DataFrame({"fips": p.fips_st_cnty, "births_nchs_3yr_avg": num(p.births_3yr_avg_23),
                         "births_ahrf_census_2024": num(p.births_july_1_june_30_24)})


def places():
    cur = pd.read_csv(os.path.join(RAW, "places_county_depression_mhlth.csv"), dtype=str)
    old = pd.read_csv(os.path.join(RAW, "places2024_county_depression_mhlth.csv"), dtype=str)
    cur["release"] = "PLACES 2025"
    old["release"] = "PLACES 2024"
    missing_states = set(old.stateabbr) - set(cur.stateabbr)
    allp = pd.concat([cur, old[old.stateabbr.isin(missing_states)]])
    rows = {}
    for (fips, meas, typ), g in allp.groupby(["locationid", "measureid", "datavaluetypeid"]):
        r = g.iloc[0]
        d = rows.setdefault(fips, {"fips": fips, "places_release": r.release, "places_brfss_year": r.year})
        key = {"DEPRESSION": "depression", "MHLTH": "mental_distress"}[meas]
        if typ == "CrdPrv":
            d[f"{key}_crude_pct"] = float(r.data_value)
            d[f"{key}_crude_lcl"] = float(r.low_confidence_limit)
            d[f"{key}_crude_ucl"] = float(r.high_confidence_limit)
        else:
            d[f"{key}_ageadj_pct"] = float(r.data_value)
    return pd.DataFrame(rows.values()), sorted(missing_states)


def svi():
    s = pd.read_csv(os.path.join(RAW, "SVI_2022_US_county.csv"), dtype=str)
    out = pd.DataFrame({"fips": s.FIPS})
    for src, dst in [("RPL_THEMES", "svi_overall"), ("RPL_THEME1", "svi_socioeconomic"),
                     ("RPL_THEME2", "svi_household"), ("RPL_THEME3", "svi_minority_language"),
                     ("RPL_THEME4", "svi_housing_transport")]:
        v = num(s[src])
        out[dst] = v.where(v >= 0)  # -999 = not computed
    return out


def rurality():
    r = pd.read_csv(os.path.join(RAW, "Ruralurbancontinuumcodes2023.csv"), dtype=str, encoding="latin1")
    r = r[r.Attribute == "RUCC_2023"]
    out = pd.DataFrame({"fips": r.FIPS.str.zfill(5), "rucc_2023": num(r.Value)})
    with zipfile.ZipFile(os.path.join(RAW, "2024_Gaz_counties_national.zip")) as z:
        g = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), sep="\t", dtype=str)
    g.columns = [c.strip() for c in g.columns]
    land = pd.DataFrame({"fips": g.GEOID, "land_sqmi": num(g.ALAND_SQMI)})
    return out.merge(land, on="fips", how="outer")


def main():
    os.makedirs(PROC, exist_ok=True)
    u = universe()
    n0 = len(u)
    w = women_15_44()
    b = ahrf_births()
    pl, pl_fallback_states = places()
    sv = svi()
    ru = rurality()
    d = (u.merge(w, on="fips", how="left").merge(b, on="fips", how="left")
          .merge(pl, on="fips", how="left").merge(sv, on="fips", how="left").merge(ru, on="fips", how="left"))
    assert len(d) == n0, "join changed row count"

    # Births (DECISION 1)
    assert BIRTHS_RULE == "nchs_then_census"
    use_nchs = d.births_nchs_3yr_avg.notna()
    d["births"] = np.where(use_nchs, d.births_nchs_3yr_avg, d.births_census_2024)
    d["births_source"] = np.where(use_nchs, "NCHS 3-yr avg (AHRF births_3yr_avg_23)",
                                  "Census PEP V2024 (BIRTHS2024)")
    d["births_years"] = np.where(use_nchs, "2021-2023", "2023-07 to 2024-06")
    d["general_fertility_rate"] = (1000 * d.births / d.women_15_44).round(1)

    # Need-weighted births: births x adult depression prevalence (a proxy, not a case count)
    d["births_x_depression"] = (d.births * d.depression_crude_pct / 100).round(1)

    # Years carried with every measure
    d["women_15_44_year"] = "2024-07-01"
    d["svi_year"] = "2022 (ACS 2018-2022)"
    d["rucc_year"] = "2023"

    # Rural and frontier (DECISION 2)
    d["pop_density_2024"] = (d.pop_total_2024 / d.land_sqmi).round(2)
    d["rural"] = d.rucc_2023.isin(RURAL_RUCC).astype("Int64").where(d.rucc_2023.notna())
    d["frontier"] = (d.pop_density_2024 < FRONTIER_DENSITY).astype("Int64").where(d.pop_density_2024.notna())
    d["rurality_class"] = np.select(
        [d.frontier == 1, d.rural == 1, d.rural == 0], ["frontier", "rural", "metro"], default="unknown")

    # Flags
    d["flag_small_births"] = (d.births < SMALL_N).astype(int)
    d["flag_births_census_fallback"] = (~use_nchs).astype(int)
    d["flag_places_prior_release"] = d.places_release.eq("PLACES 2024").astype(int)
    d["flag_missing_depression"] = d.depression_crude_pct.isna().astype(int)
    d["flag_missing_svi"] = d.svi_overall.isna().astype(int)

    cols = ["fips", "state_fips", "state", "county_name", "pop_total_2024", "women_15_44", "women_15_44_year",
            "births", "births_source", "births_years", "births_nchs_3yr_avg", "births_census_2024",
            "general_fertility_rate", "depression_crude_pct", "depression_crude_lcl", "depression_crude_ucl",
            "depression_ageadj_pct", "mental_distress_crude_pct", "mental_distress_ageadj_pct",
            "places_release", "places_brfss_year", "births_x_depression",
            "svi_overall", "svi_socioeconomic", "svi_household", "svi_minority_language",
            "svi_housing_transport", "svi_year", "rucc_2023", "rucc_year", "land_sqmi", "pop_density_2024",
            "rural", "frontier", "rurality_class", "flag_small_births", "flag_births_census_fallback",
            "flag_places_prior_release", "flag_missing_depression", "flag_missing_svi"]
    d = d[cols].sort_values("fips")
    d.to_csv(os.path.join(PROC, "need_county.csv"), index=False)
    with open(os.path.join(PROC, "need_build_notes.txt"), "w") as f:
        f.write(f"rows={len(d)}\nplaces_fallback_states={','.join(pl_fallback_states)}\n")
    print(len(d), "counties; PLACES fallback states:", pl_fallback_states)
    print(d[["births", "depression_crude_pct", "svi_overall", "rucc_2023", "land_sqmi", "women_15_44"]].isna().sum())


if __name__ == "__main__":
    main()
