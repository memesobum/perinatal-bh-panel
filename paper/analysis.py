#!/usr/bin/env python3
"""paper/analysis.py: every number and table in the preprint, computed from data/processed.

Plain-language summary: reads the released county tables, runs the comparisons,
statistical tests and sensitivity checks reported in the paper, and writes
paper/paper_stats.json (every number the manuscript quotes) and LaTeX tables in
paper/tables/. Nothing in the manuscript is typed by hand.
"""
import io, json, os, sys, zipfile
import numpy as np, pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from config import PROC, RAW  # noqa: E402

OUT = os.path.join(ROOT, "paper")
TAB = os.path.join(OUT, "tables"); os.makedirs(TAB, exist_ok=True)
d = pd.read_csv(os.path.join(PROC, "panel_county.csv"), dtype={"fips": str})
fac = pd.read_csv(os.path.join(PROC, "capacity_facilities.csv"), dtype={"fips": str})
base = json.load(open(os.path.join(ROOT, "report", "stats.json")))
S = {}
CLS = ["metro", "rural", "frontier"]

def pr(s):
    return 100 * s.rank(method="average", pct=True)

def scores(df, need_cols, cap_cols, elig=None):
    df = df.copy()
    if elig is None:
        elig = pd.Series(True, index=df.index)
    need = pd.concat([pr(df[c].where(elig)) for c in need_cols], axis=1).mean(axis=1)
    cap = pd.concat([pr(df[c].where(elig)) for c in cap_cols], axis=1).mean(axis=1)
    return need, cap, need - cap

def hnlc(need, cap):
    return (need >= need.quantile(0.75)) & (cap <= cap.quantile(0.25))

# ---- baseline reproduction check
need0, cap0, gap0 = scores(d, ["depression_crude_pct", "svi_overall"],
                           ["ppw_sud_facilities_per_1k_births", "bh_clinicians_per_1k_births",
                            "ob_clinicians_per_1k_births", "hc_sites_per_1k_births"])
S["baseline_reproduces_max_abs_diff"] = float((gap0.round(1) - d.gap_score).abs().max())
h0 = hnlc(need0, cap0)

# ---- rurality summary table
rows = []
for c in CLS + ["all"]:
    g = d if c == "all" else d[d.rurality_class == c]
    rows.append({
        "class": c, "n": len(g), "births": g.births.sum(), "women": g.women_15_44.sum(),
        "pct_births": 100 * g.births.sum() / d.births.sum(),
        "dep_med": g.depression_crude_pct.median(), "svi_med": g.svi_overall.median(),
        "no_ppw": 100 * g.no_ppw_sud_facility.mean(), "no_bhp": 100 * g.no_bh_prescriber.mean(),
        "no_ob": 100 * g.no_ob_clinician.mean(), "no_hc": 100 * (g.hc_sites == 0).mean(),
        "bh_per_1k_med": g.bh_clinicians_per_1k_births.median(),
        "ob_per_1k_med": g.ob_clinicians_per_1k_births.median(),
        "need_med": g.need_score.median(), "cap_med": g.capacity_score.median(), "gap_med": g.gap_score.median(),
        "hnlc": int(g.high_need_low_capacity.sum()),
        "births_no_ppw": g.loc[g.no_ppw_sud_facility == 1, "births"].sum(),
    })
R = pd.DataFrame(rows).set_index("class")
S["rurality"] = json.loads(R.round(6).to_json(orient="index"))

# national-level totals of capacity
S["tot"] = {k: int(d[k].sum()) for k in ["ppw_sud_facilities", "ppw_sud_locations", "tx_listings_all",
            "tx_locations_all", "tx_listings_mh", "tx_listings_sa", "tx_listings_otp", "hc_sites", "hc_locations",
            "ob_clinicians", "bh_prescribers", "bh_therapists", "family_medicine_physicians",
            "ppw_sud_facilities_medicaid", "ppw_sud_facilities_moud", "childcare_facilities",
            "res_child_beds_facilities"]}
S["share_sa_listings_ppw"] = round(100 * fac[(fac.facility_type == "SA") & fac.fips.notna()].serves_ppw.mean(), 1)
p = fac[(fac.serves_ppw == 1) & fac.fips.notna()]
S["ppw_pct_medicaid"] = round(100 * p.accepts_medicaid.mean(), 1)
S["ppw_pct_moud"] = round(100 * p.offers_moud.mean(), 1)
S["ppw_pct_childcare"] = round(100 * p.childcare_for_clients.mean(), 1)
S["ppw_pct_resbeds"] = round(100 * p.residential_beds_for_children.mean(), 1)
S["n_no_ob_clinician"] = int(d.no_ob_clinician.sum())
S["n_no_hc"] = int((d.hc_sites == 0).sum())
S["n_no_any"] = int(((d.ppw_sud_facilities == 0) & (d.bh_prescribers == 0) & (d.ob_clinicians == 0)).sum())
S["births_no_any"] = int(d.loc[(d.ppw_sud_facilities == 0) & (d.bh_prescribers == 0) & (d.ob_clinicians == 0), "births"].sum())

# ---- tests
kw = stats.kruskal(*[d.loc[d.rurality_class == c, "gap_score"].dropna() for c in CLS])
S["kw_gap_H"], S["kw_gap_p"] = round(float(kw.statistic), 1), float(kw.pvalue)
ct = pd.crosstab(d.rurality_class, d.no_ppw_sud_facility)
chi = stats.chi2_contingency(ct)
S["chi_noppw"], S["chi_noppw_p"], S["chi_noppw_dof"] = round(float(chi[0]), 1), float(chi[1]), int(chi[2])
m = d[["need_score", "capacity_score"]].dropna()
rho = stats.spearmanr(m.need_score, m.capacity_score)
S["rho_need_cap"], S["rho_need_cap_p"] = round(float(rho.statistic), 3), float(rho.pvalue)
for comp in ["depression_crude_pct", "svi_overall"]:
    r_ = stats.spearmanr(d[comp], d.capacity_score, nan_policy="omit")
    S[f"rho_{comp}_cap"] = round(float(r_.statistic), 3)
r_ = stats.spearmanr(d.depression_crude_pct, d.svi_overall, nan_policy="omit")
S["rho_dep_svi"] = round(float(r_.statistic), 3)
mw = stats.mannwhitneyu(d.loc[d.no_ppw_sud_facility == 1, "need_score"].dropna(),
                        d.loc[d.no_ppw_sud_facility == 0, "need_score"].dropna())
S["need_med_noppw"] = round(float(d.loc[d.no_ppw_sud_facility == 1, "need_score"].median()), 1)
S["need_med_ppw"] = round(float(d.loc[d.no_ppw_sud_facility == 0, "need_score"].median()), 1)
S["mw_need_p"] = float(mw.pvalue)
# small-county instability
sm, bg = d[d.births < 20], d[d.births > 2000]
S["cap_med_small"], S["cap_med_big"] = round(float(sm.capacity_score.median()), 1), round(float(bg.capacity_score.median()), 1)
S["gap_iqr_small"] = round(float(sm.gap_score.quantile(.75) - sm.gap_score.quantile(.25)), 1)
S["gap_iqr_big"] = round(float(bg.gap_score.quantile(.75) - bg.gap_score.quantile(.25)), 1)
S["n_births_lt20"], S["n_births_gt2000"] = int(len(sm)), int(len(bg))

# ---- sensitivity analyses
sens = []
def add(label, need_cols, cap_cols, frame=d, elig=None, note=""):
    n_, c_, g_ = scores(frame, need_cols, cap_cols, elig)
    ok = g_.notna() & gap0.notna()
    rs = stats.spearmanr(g_[ok], gap0[ok]).statistic
    h = hnlc(n_, c_)
    jac = (h & h0).sum() / (h | h0).sum()
    st = g_[d.fips == "32029"].iloc[0]
    sens.append({"label": label, "rho": round(float(rs), 3), "n_hnlc": int(h.sum()),
                 "overlap": int((h & h0).sum()), "jaccard": round(float(jac), 2),
                 "storey": None if pd.isna(st) else round(float(st), 1), "note": note})
NEED = ["depression_crude_pct", "svi_overall"]
CAP = ["ppw_sud_facilities_per_1k_births", "bh_clinicians_per_1k_births", "ob_clinicians_per_1k_births", "hc_sites_per_1k_births"]
add("Baseline", NEED, CAP)
w = d.copy()
for k, src in [("a", "ppw_sud_facilities"), ("b", "bh_clinicians"), ("c", "ob_clinicians"), ("e", "hc_sites")]:
    w[f"{src}_pw"] = 1000 * w[src] / w.women_15_44
add("Capacity per 1,000 women aged 15-44", NEED, [f"{s}_pw" for s in ["ppw_sud_facilities", "bh_clinicians", "ob_clinicians", "hc_sites"]], frame=w)
add("Counties with <20 births unranked", NEED, CAP, elig=d.births >= 20)
w["hcloc_pb"] = 1000 * w.hc_locations / w.births
w["ppwloc_pb"] = 1000 * w.ppw_sud_locations / w.births
add("Health centers counted by address", NEED, [CAP[0], CAP[1], CAP[2], "hcloc_pb"], frame=w)
add("PPW programs counted by address", NEED, ["ppwloc_pb"] + CAP[1:], frame=w)
add("Age-adjusted depression", ["depression_ageadj_pct", "svi_overall"], CAP)
add("Need adds frequent mental distress", NEED + ["mental_distress_crude_pct"], CAP)
add("Capacity adds MH listings", NEED, CAP + ["mh_listings_per_1k_births"])
w["bhp_pb"] = w.bh_prescribers_per_1k_births
add("Behavioral prescribers only", NEED, [CAP[0], "bhp_pb", CAP[2], CAP[3]], frame=w)
SENS = pd.DataFrame(sens)
S["sensitivity"] = sens

# ---- states
st = d.groupby("state").apply(lambda g: pd.Series({
    "n": len(g), "births": g.births.sum(),
    "pct_cty_noppw": 100 * g.no_ppw_sud_facility.mean(),
    "pct_births_noppw": 100 * g.loc[g.no_ppw_sud_facility == 1, "births"].sum() / g.births.sum(),
    "hnlc": g.high_need_low_capacity.sum(),
    "ppw_per_10k_births": 1e4 * g.ppw_sud_facilities.sum() / g.births.sum()}), include_groups=False)
st.to_csv(os.path.join(TAB, "state_summary.csv"))
S["n_states_all_cty_have_ppw"] = int((st.pct_cty_noppw == 0).sum())
S["states_top5_births_noppw"] = st.sort_values("pct_births_noppw", ascending=False).head(5).round(1).reset_index()[["state", "pct_births_noppw"]].values.tolist()
S["states_zero_births_noppw"] = sorted(st[st.pct_births_noppw == 0].index.tolist())
S["state_ppw_per10k_range"] = [round(float(st.ppw_per_10k_births.min()), 1), st.ppw_per_10k_births.idxmin(),
                               round(float(st.ppw_per_10k_births.max()), 1), st.ppw_per_10k_births.idxmax()]
S["state_ppw_per10k_median"] = round(float(st.ppw_per_10k_births.median()), 1)
S["hnlc_states"] = st.sort_values("hnlc", ascending=False).head(5).reset_index()[["state", "hnlc"]].astype({"hnlc": int}).values.tolist()
S["n_states_with_hnlc"] = int((st.hnlc > 0).sum())

# ---- validation vs AHRF
with zipfile.ZipFile(os.path.join(RAW, "AHRF_2024-2025_CSV.zip")) as z:
    n = [x for x in z.namelist() if x.endswith("AHRF2025hp.csv")][0]
    h = pd.read_csv(io.BytesIO(z.read(n)), dtype=str, encoding="latin1",
                    usecols=["fips_st_cnty", "md_nf_obgyn_gen_all_pc_23", "md_nf_obgyn_subsp_all_pc_23", "md_nf_psych_all_pc_23"])
a = pd.DataFrame({"fips": h.fips_st_cnty,
                  "ahrf_ob": pd.to_numeric(h.md_nf_obgyn_gen_all_pc_23, errors="coerce") + pd.to_numeric(h.md_nf_obgyn_subsp_all_pc_23, errors="coerce"),
                  "ahrf_psy": pd.to_numeric(h.md_nf_psych_all_pc_23, errors="coerce")})
v = d.merge(a, on="fips")
v.to_csv(os.path.join(OUT, "validation_ahrf.csv"), index=False, columns=["fips", "ob_clinicians", "ahrf_ob", "bh_prescribers", "ahrf_psy", "rurality_class"])
vo, vp = v[["ob_clinicians", "ahrf_ob"]].dropna(), v[["bh_prescribers", "ahrf_psy"]].dropna()
S["val_r_ob"] = round(float(np.corrcoef(np.log1p(vo.iloc[:, 0]), np.log1p(vo.iloc[:, 1]))[0, 1]), 3)
S["val_r_psy"] = round(float(np.corrcoef(np.log1p(vp.iloc[:, 0]), np.log1p(vp.iloc[:, 1]))[0, 1]), 3)
S["val_rho_ob"] = round(float(stats.spearmanr(vo.iloc[:, 0], vo.iloc[:, 1]).statistic), 3)
S["val_rho_psy"] = round(float(stats.spearmanr(vp.iloc[:, 0], vp.iloc[:, 1]).statistic), 3)
S["val_n"] = int(len(vo))
S["val_sum_ob_nppes"], S["val_sum_ob_ahrf"] = int(vo.iloc[:, 0].sum()), int(vo.iloc[:, 1].sum())
S["val_sum_psy_nppes"], S["val_sum_psy_ahrf"] = int(vp.iloc[:, 0].sum()), int(vp.iloc[:, 1].sum())
S["val_agree_zero_ob"] = round(float(100 * ((vo.iloc[:, 0] == 0) == (vo.iloc[:, 1] == 0)).mean()), 1)
S["val_agree_zero_psy"] = round(float(100 * ((vp.iloc[:, 0] == 0) == (vp.iloc[:, 1] == 0)).mean()), 1)

# ---- top-gap counties and Nevada
top = d[d.ranked == 1].nlargest(15, "gap_score")
top[["fips", "county_name", "state", "rurality_class", "births", "depression_crude_pct", "svi_overall",
     "ppw_sud_facilities", "bh_clinicians", "ob_clinicians", "hc_sites", "need_score", "capacity_score",
     "gap_score"]].to_csv(os.path.join(TAB, "top15_gap.csv"), index=False)
S["top15_small_births"] = int((top.births < 20).sum())
top20 = d[d.births >= 20].nlargest(15, "gap_score")
S["top15_states"] = top.state.value_counts().to_dict()
dnv = d[d.state == "NV"].sort_values("county_name")
dnv.to_csv(os.path.join(TAB, "nevada.csv"), index=False)
S["nv"] = {"births": int(dnv.births.sum()), "n_no_ppw": int(dnv.no_ppw_sud_facility.sum()),
           "n_frontier": int((dnv.rurality_class == "frontier").sum()), "ppw_total": int(dnv.ppw_sud_facilities.sum()),
           "pct_births_noppw": round(float(100 * dnv.loc[dnv["no_ppw_sud_facility"] == 1, "births"].sum() / dnv.births.sum()), 1),
           "n_no_ob": int(dnv.no_ob_clinician.sum()), "n_no_bhp": int(dnv.no_bh_prescriber.sum()),
           "clark_washoe_share_births": round(float(100 * dnv[dnv["county_name"].isin(["Clark County", "Washoe County"])].births.sum() / dnv.births.sum()), 1),
           "clark_washoe_share_ppw": round(float(100 * dnv[dnv["county_name"].isin(["Clark County", "Washoe County"])].ppw_sud_facilities.sum() / dnv.ppw_sud_facilities.sum()), 1)}

S["base"] = base
json.dump(S, open(os.path.join(OUT, "paper_stats.json"), "w"), indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
R.to_csv(os.path.join(TAB, "rurality_summary.csv"))
SENS.to_csv(os.path.join(TAB, "sensitivity.csv"), index=False)
print(json.dumps({k: v for k, v in S.items() if k not in ("base", "rurality", "sensitivity")}, indent=1, default=str))
print(R.round(1).T)
print(SENS)
