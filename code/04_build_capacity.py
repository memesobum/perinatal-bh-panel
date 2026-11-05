#!/usr/bin/env python3
"""04_build_capacity.py: build the capacity inventory (Release 2).

Plain-language summary: puts every treatment facility, health center site,
and counted clinician into a county, then counts them per county. Writes:
  data/processed/capacity_facilities.csv   one row per FindTreatment.gov listing, with service flags
  data/processed/capacity_hc_sites.csv     one row per counted HRSA health center site
  data/processed/capacity_clinicians_by_zip.csv   clinician counts by ZIP and group (no names)
  data/processed/capacity_county.csv       county totals of everything above
The rules for what counts are in docs/CODING_RULES.md.
"""

import hashlib
import json
import os
import sys
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import (FT_CHILDCARE, FT_PPW, FT_RES_CHILD_BEDS, FT_WOMEN, PROC, RAW, STATE_ABBR)  # noqa: E402

HC_TYPES_KEEP = {"Service Delivery Site", "Administrative/Service Delivery Site"}
HC_LOC_KEEP = {"Permanent"}
HC_SETTING_DROP = {"School", "Correctional Facility", "Transitional Care in Carceral Setting"}


def counties_gdf():
    g = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_county_500k.zip')}")
    return g[["GEOID", "geometry"]].rename(columns={"GEOID": "fips"}).to_crs(4326)


def has(services, code_val):
    code, val = code_val
    for s in services or []:
        if s.get("f2") == code and val in (s.get("f3") or "").split("; "):
            return 1
    return 0


def field(services, code):
    for s in services or []:
        if s.get("f2") == code:
            return s.get("f3") or ""
    return ""


def facilities(cg, zl):
    with open(os.path.join(RAW, "findtreatment_all_states.json")) as f:
        raw = json.load(f)
    recs = []
    for st, blob in raw.items():
        for r in blob["rows"]:
            sv = r.get("services")
            key = "|".join(str(r.get(k) or "").strip().lower() for k in ["name1", "street1", "zip", "typeFacility"])
            pay = field(sv, "PAY")
            lkey = "|".join(str(r.get(k) or "").strip().lower() for k in ["street1", "zip"])
            recs.append({
                "facility_id": hashlib.sha1(key.encode()).hexdigest()[:12],
                "location_id": hashlib.sha1(lkey.encode()).hexdigest()[:12],
                "query_state": st, "name": r.get("name1"), "name2": r.get("name2"),
                "street": r.get("street1"), "city": r.get("city"), "state": r.get("state"),
                "zip": (r.get("zip") or "")[:5], "phone": r.get("phone"), "website": r.get("website"),
                "latitude": pd.to_numeric(r.get("latitude"), errors="coerce"),
                "longitude": pd.to_numeric(r.get("longitude"), errors="coerce"),
                "facility_type": r.get("typeFacility"),
                "serves_ppw": has(sv, FT_PPW), "serves_adult_women": has(sv, FT_WOMEN),
                "childcare_for_clients": has(sv, FT_CHILDCARE),
                "residential_beds_for_children": has(sv, FT_RES_CHILD_BEDS),
                "accepts_medicaid": int("Medicaid" in pay.split("; ")),
                "offers_moud": int(bool(field(sv, "OM"))),
                "service_setting": field(sv, "SET"),
                "services_listed": int(sv is not None),
            })
    df = pd.DataFrame(recs)
    n_raw = len(df)
    df = df.drop_duplicates("facility_id")
    pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=4326)
    j = gpd.sjoin(pts, cg, how="left", predicate="within").drop(columns=["index_right"])
    j = j[~j.index.duplicated()]
    # Fallback for points just outside a polygon (coastline, border): nearest county within 2 km
    miss = j.fips.isna() & j.latitude.notna()
    if miss.any():
        near = gpd.sjoin_nearest(pts.loc[miss[miss].index].to_crs(5070), cg.to_crs(5070), how="left",
                                 max_distance=2000, distance_col="d_m")
        near = near[~near.index.duplicated()]
        j.loc[near.index, "fips"] = near.fips
        j.loc[near.index, "geo_method"] = "nearest_within_2km"
    if "geo_method" not in j.columns:
        j["geo_method"] = None
    j.loc[j.fips.notna() & j.geo_method.isna(), "geo_method"] = "point_in_polygon"
    # Listings with no coordinates: place by ZIP (same ZIP rule as clinicians)
    nz = j.fips.isna()
    j.loc[nz, "fips"] = j.loc[nz, "zip"].map(zl[0])
    j.loc[nz & j.fips.notna(), "geo_method"] = "zip_to_county"
    # State check: coordinates sometimes point to a same-named town in another state
    # (e.g. Hartford, VT geocoded to Hartford, CT). If the county's state differs from the
    # listing's state, re-place by ZIP; keep the ZIP result only if it is in the listed state.
    cst = j.fips.str[:2].map(STATE_ABBR)
    bad = j.fips.notna() & (cst != j.state)
    zf = j.loc[bad, "zip"].map(zl[0])
    ok = zf.notna() & (zf.str[:2].map(STATE_ABBR) == j.loc[bad, "state"])
    j.loc[bad, "fips"] = zf.where(ok)
    j.loc[bad, "geo_method"] = np.where(ok, "zip_to_county_after_state_mismatch", "unassigned")
    j.loc[j.fips.isna(), "geo_method"] = "unassigned"
    out = pd.DataFrame(j.drop(columns="geometry"))
    out.to_csv(os.path.join(PROC, "capacity_facilities.csv"), index=False)
    return out, n_raw


def hc_sites(zl):
    h = pd.read_csv(os.path.join(RAW, "Health_Center_Service_Delivery_and_LookAlike_Sites.csv"), dtype=str)
    n_raw = len(h)
    h = h[(h["Site Status Description"] == "Active")
          & h["Health Center Type Description"].isin(HC_TYPES_KEEP)
          & h["Health Center Location Type Description"].isin(HC_LOC_KEEP)
          & ~h["Health Center Service Delivery Site Location Setting Description"].isin(HC_SETTING_DROP)]
    out = pd.DataFrame({
        "bphc_site_id": h["BPHC Assigned Number"], "site_name": h["Site Name"],
        "health_center_name": h["Health Center Name"], "health_center_type": h["Health Center Type"],
        "address": h["Site Address"], "city": h["Site City"], "state": h["Site State Abbreviation"],
        "zip": h["Site Postal Code"].str[:5], "fips": h["State and County Federal Information Processing Standard Code"],
        "longitude": pd.to_numeric(h["Geocoding Artifact Address Primary X Coordinate"], errors="coerce"),
        "latitude": pd.to_numeric(h["Geocoding Artifact Address Primary Y Coordinate"], errors="coerce"),
        "setting": h["Health Center Service Delivery Site Location Setting Description"],
        "operating_hours_per_week": pd.to_numeric(h["Operating Hours per Week"], errors="coerce"),
    })
    out["fips"] = out.fips.str.strip().replace("", np.nan)  # HRSA pads missing codes with spaces
    out["geo_method"] = np.where(out.fips.notna(), "hrsa_county_code", None)
    nz = out.fips.isna() & out.zip.notna()
    out.loc[nz, "fips"] = out.loc[nz, "zip"].map(zl[0])
    out.loc[nz & out.fips.notna(), "geo_method"] = "zip_to_county"
    # HRSA publishes no address (state "XX") for some sites; these cannot be placed.
    out.loc[out.fips.isna(), "geo_method"] = np.where(out.loc[out.fips.isna(), "state"] == "XX",
                                                      "unplaced_no_address_in_hrsa_file", "unassigned")
    loc = (out.address.fillna("").str.lower().str.replace(r"[^a-z0-9]", "", regex=True) + "|" + out.zip.fillna(""))
    out["location_id"] = [hashlib.sha1(x.encode()).hexdigest()[:12] for x in loc]
    out.to_csv(os.path.join(PROC, "capacity_hc_sites.csv"), index=False)
    return out, n_raw


def zip_to_county():
    """ZCTA -> county with the largest land-area overlap (Census 2020 relationship file)."""
    r = pd.read_csv(os.path.join(RAW, "tab20_zcta520_county20_natl.txt"), sep="|", dtype=str, encoding="utf-8-sig")
    r = r[r.GEOID_ZCTA5_20.notna() & (r.GEOID_ZCTA5_20 != "")]
    r["part"] = pd.to_numeric(r.AREALAND_PART, errors="coerce").fillna(0)
    tot = r.groupby("GEOID_ZCTA5_20").part.transform("sum")
    r["share"] = np.where(tot > 0, r.part / tot, 0)
    r = r.sort_values(["GEOID_ZCTA5_20", "share"], ascending=[True, False])
    best = r.drop_duplicates("GEOID_ZCTA5_20")
    m = dict(zip(best.GEOID_ZCTA5_20, best.GEOID_COUNTY_20))
    share = dict(zip(best.GEOID_ZCTA5_20, best.share))
    return m, share


def zip_lookup(cg):
    """Return (fips_map, share_map, method_map) for 5-digit ZIPs.

    Most ZIPs: ZCTA -> county with the largest land overlap (2020 relationship file).
    Connecticut: the 2020 file still uses the old 8 counties, so CT ZCTAs are placed in
    2022 planning regions by their 2024 Gazetteer interior point.
    """
    m, share = zip_to_county()
    method = {z: "zcta_largest_land" for z in m}
    zg = ct_zcta_points()
    if zg is not None:
        pts = gpd.GeoDataFrame(zg, geometry=gpd.points_from_xy(zg.lon, zg.lat), crs=4326)
        jj = gpd.sjoin(pts, cg[cg.fips.str.startswith("09")], how="inner", predicate="within")
        for z in [k for k, v in m.items() if v.startswith("09")]:
            m.pop(z)
            method.pop(z)
        for z, fp in zip(jj.zcta, jj.fips):
            m[z] = fp
            share[z] = np.nan
            method[z] = "ct_zcta_point_to_planning_region"
    return m, share, method


def clinicians(cg, zl):
    c = pd.read_csv(os.path.join(PROC, "nppes_clinicians.csv"), dtype=str)
    n_raw = len(c)
    c = c[(c.practice_country.isna()) | (c.practice_country == "") | (c.practice_country == "US")]
    m, share, method = zl
    c["fips"] = c.zip5.map(m)
    c["zip_county_share"] = c.zip5.map(share)
    c["zip_match"] = c.zip5.map(method).fillna("unmatched")
    byzip = c.groupby(["zip5", "fips", "group"], dropna=False).size().rename("clinicians").reset_index()
    byzip.to_csv(os.path.join(PROC, "capacity_clinicians_by_zip.csv"), index=False)
    return c, n_raw


def ct_zcta_points():
    """ZCTA interior points (2024 Gazetteer). Used only to place Connecticut ZCTAs in planning regions,
    because the 2020 ZCTA-county relationship file still uses Connecticut's old 8 counties."""
    p = os.path.join(RAW, "2024_Gaz_zcta_national.zip")
    if not os.path.exists(p):
        return None
    with zipfile.ZipFile(p) as z:
        g = pd.read_csv(z.open(z.namelist()[0]), sep="\t", dtype=str)
    g.columns = [x.strip() for x in g.columns]
    return pd.DataFrame({"zcta": g.GEOID, "lat": pd.to_numeric(g.INTPTLAT), "lon": pd.to_numeric(g.INTPTLONG)})


def main():
    cg = counties_gdf()
    zl = zip_lookup(cg)
    fac, fac_raw = facilities(cg, zl)
    hc, hc_raw = hc_sites(zl)
    cl, cl_raw = clinicians(cg, zl)

    need = pd.read_csv(os.path.join(PROC, "need_county.csv"), dtype={"fips": str})
    cty = need[["fips", "state", "county_name", "births"]].copy()

    f = fac[fac.fips.notna()]
    agg = f.groupby("fips").agg(
        tx_listings_all=("facility_id", "size"),
        tx_locations_all=("location_id", "nunique"),
        tx_listings_mh=("facility_type", lambda s: (s == "MH").sum()),
        tx_listings_sa=("facility_type", lambda s: (s == "SA").sum()),
        tx_listings_otp=("facility_type", lambda s: (s == "OTP").sum()),
        ppw_sud_facilities=("serves_ppw", "sum"),
        women_program_facilities=("serves_adult_women", "sum"),
        childcare_facilities=("childcare_for_clients", "sum"),
        res_child_beds_facilities=("residential_beds_for_children", "sum"),
    ).reset_index()
    ppw_loc = f[f.serves_ppw == 1].groupby("fips").location_id.nunique().rename("ppw_sud_locations").reset_index()
    ppw_medicaid = f[(f.serves_ppw == 1) & (f.accepts_medicaid == 1)].groupby("fips").size().rename(
        "ppw_sud_facilities_medicaid").reset_index()
    ppw_moud = f[(f.serves_ppw == 1) & (f.offers_moud == 1)].groupby("fips").size().rename(
        "ppw_sud_facilities_moud").reset_index()
    hca = hc[hc.fips.notna()].groupby("fips").agg(hc_sites=("bphc_site_id", "size"),
                                                  hc_locations=("location_id", "nunique")).reset_index()
    cla = cl[cl.fips.notna()].pivot_table(index="fips", columns="group", values="npi", aggfunc="size",
                                          fill_value=0).reset_index()
    cla = cla.rename(columns={"obstetric": "ob_clinicians", "bh_prescriber": "bh_prescribers",
                              "bh_therapist": "bh_therapists", "family_medicine": "family_medicine_physicians"})
    for x in [agg, ppw_loc, ppw_medicaid, ppw_moud, hca, cla]:
        cty = cty.merge(x, on="fips", how="left")
    countcols = [c for c in cty.columns if c not in ("fips", "state", "county_name", "births")]
    cty[countcols] = cty[countcols].fillna(0).astype(int)
    cty["bh_clinicians"] = cty.bh_prescribers + cty.bh_therapists
    per = lambda n: (1000 * n / cty.births).replace([np.inf, -np.inf], np.nan).round(2)  # noqa: E731
    cty["ppw_sud_facilities_per_1k_births"] = per(cty.ppw_sud_facilities)
    cty["mh_listings_per_1k_births"] = per(cty.tx_listings_mh)
    cty["bh_clinicians_per_1k_births"] = per(cty.bh_clinicians)
    cty["bh_prescribers_per_1k_births"] = per(cty.bh_prescribers)
    cty["ob_clinicians_per_1k_births"] = per(cty.ob_clinicians)
    cty["hc_sites_per_1k_births"] = per(cty.hc_sites)
    cty["no_ppw_sud_facility"] = (cty.ppw_sud_facilities == 0).astype(int)
    cty["no_bh_prescriber"] = (cty.bh_prescribers == 0).astype(int)
    cty["no_ob_clinician"] = (cty.ob_clinicians == 0).astype(int)
    cty["flag_small_count_ppw_sud"] = ((cty.ppw_sud_facilities > 0) & (cty.ppw_sud_facilities < 3)).astype(int)
    cty["findtreatment_access_date"] = "2026-11-04"
    cty["nppes_file"] = "NPPES V.2 November 2026 (2026-11-02)"
    cty["hrsa_sites_file_date"] = "2026-11-04"
    cty = cty.drop(columns=["births"])
    cty.to_csv(os.path.join(PROC, "capacity_county.csv"), index=False)

    stats = {
        "ft_rows_raw": int(fac_raw), "ft_unique": int(len(fac)),
        "ft_assigned": int(fac.fips.notna().sum()),
        "ft_geo_method": fac.geo_method.value_counts().to_dict(),
        "ft_ppw_total": int(fac.serves_ppw.sum()),
        "ft_type_counts": fac.facility_type.value_counts().to_dict(),
        "ft_assigned_outside_universe": int((~fac.fips.dropna().isin(need.fips)).sum()),
        "hc_rows_raw": int(hc_raw), "hc_kept": int(len(hc)),
        "hc_geo_method": hc.geo_method.value_counts().to_dict(),
        "hc_in_territories": int((hc.fips.notna() & ~hc.fips.isin(need.fips)).sum()),
        "hc_in_panel": int(hc.fips.isin(need.fips).sum()),
        "hc_in_panel_locations": int(hc[hc.fips.isin(need.fips)].location_id.nunique()),
        "ft_locations": int(fac[fac.fips.notna()].location_id.nunique()),
        "ft_state_mismatch_fixed": int((fac.geo_method == "zip_to_county_after_state_mismatch").sum()),
        "nppes_kept_raw": int(cl_raw), "nppes_us": int(len(cl)),
        "nppes_zip_match": cl.zip_match.value_counts().to_dict(),
        "nppes_outside_universe": int((cl.fips.notna() & ~cl.fips.isin(need.fips)).sum()),
        "nppes_group_counts": cl.group.value_counts().to_dict(),
    }
    with open(os.path.join(PROC, "capacity_build_stats.json"), "w") as fjson:
        json.dump(stats, fjson, indent=2, default=int)
    print(json.dumps(stats, indent=2, default=int))


if __name__ == "__main__":
    main()
