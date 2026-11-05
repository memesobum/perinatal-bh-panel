#!/usr/bin/env python3
"""paper/make_tex_inputs.py: turn paper_stats.json and the table CSVs into LaTeX macros and tables.
Every number the manuscript prints comes from here (stats-file rule)."""
import json, os
import pandas as pd
H = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(H, "paper_stats.json"))); B = S["base"]; R = S["rurality"]; T = S["tot"]
def c(x): return f"{int(round(x)):,}".replace(",", "{,}")
def f1(x): return f"{x:.1f}"
def f2(x): return f"{x:.2f}"
def f3(x): return f"{x:.3f}"
def pexp(p):
    if p == 0: return "<10^{-300}"
    e = int(f"{p:.0e}".split("e")[1]); return f"<10^{{{e + 1}}}"
M = {
 "NCounties": c(B["n_counties"]), "NMetro": c(B["n_metro"]), "NRural": c(B["n_rural"]), "NFrontier": c(B["n_frontier"]),
 "BirthsTotal": c(B["births_total"]), "NFallback": c(B["n_births_fallback_ct"] + B["n_births_fallback_suppressed"]),
 "NFallbackSupp": c(B["n_births_fallback_suppressed"]), "NPlacesPrior": c(B["n_places_prior_release"]),
 "NSmallBirths": c(B["n_small_births"]), "FTUnique": c(B["ft_unique"]), "FTRaw": "27{,}506", "FTLocations": c(B["ft_locations"]),
 "FTPPW": c(B["ft_ppw_total"]), "FTPPWPlaced": c(T["ppw_sud_facilities"]), "FTPPWLoc": c(T["ppw_sud_locations"]),
 "FTAssignedPct": f1(B["ft_assigned_pct"]), "FTUnassigned": c(B["ft_unassigned"]), "FTMismatch": c(B["ft_state_mismatch_fixed"]),
 "FTMH": "12{,}637", "FTSA": "12{,}047", "FTOTP": "1{,}958",
 "ShareSAPPW": f1(S["share_sa_listings_ppw"]), "PPWMedicaid": f1(S["ppw_pct_medicaid"]), "PPWMOUD": f1(S["ppw_pct_moud"]),
 "PPWChildcare": f1(S["ppw_pct_childcare"]), "PPWResbeds": f1(S["ppw_pct_resbeds"]),
 "HCSites": c(B["hc_sites_counted"]), "HCLocations": c(B["hc_locations_counted"]), "HCUnplaced": c(B["hc_unplaced_no_address"]),
 "Clinicians": c(B["clinicians_counted"]), "OBTotal": c(B["ob_clinicians_total"]), "BHPTotal": c(B["bh_prescribers_total"]),
 "BHTTotal": c(B["bh_therapists_total"]), "FMTotal": c(B["family_medicine_total"]),
 "NNoPPW": c(B["n_no_ppw_sud_facility"]), "PctNoPPW": f1(B["pct_no_ppw_sud_facility"]),
 "PctBirthsNoPPW": f1(B["pct_births_in_no_ppw_counties"]), "BirthsNoPPW": c(R["all"]["births_no_ppw"]),
 "NNoBHP": c(B["n_no_bh_prescriber"]), "NNoOB": c(S["n_no_ob_clinician"]), "NNoHC": c(S["n_no_hc"]),
 "NNoAny": c(S["n_no_any"]), "BirthsNoAny": c(S["births_no_any"]),
 "NHNLC": c(B["n_high_need_low_capacity"]), "HNLCRural": c(B["high_need_low_capacity_by_class"]["rural"]),
 "HNLCFrontier": c(B["high_need_low_capacity_by_class"]["frontier"]), "HNLCMetro": c(B["high_need_low_capacity_by_class"]["metro"]),
 "HNLCNonmetro": c(B["high_need_low_capacity_nonmetro_rucc"]),
 "KWH": f1(S["kw_gap_H"]), "KWp": pexp(S["kw_gap_p"]), "ChiSq": f1(S["chi_noppw"]), "Chip": pexp(S["chi_noppw_p"]),
 "RhoNeedCap": f2(S["rho_need_cap"]), "RhoNeedCapp": pexp(S["rho_need_cap_p"]), "RhoDepSVI": f2(S["rho_dep_svi"]),
 "RhoDepCap": f2(S["rho_depression_crude_pct_cap"]), "RhoSVICap": f2(S["rho_svi_overall_cap"]),
 "NeedMedNoPPW": f1(S["need_med_noppw"]), "NeedMedPPW": f1(S["need_med_ppw"]), "MWp": pexp(S["mw_need_p"]),
 "CapMedSmall": f1(S["cap_med_small"]), "CapMedBig": f1(S["cap_med_big"]), "NBirthsBig": c(S["n_births_gt2000"]),
 "ValROB": f2(S["val_r_ob"]), "ValRPsy": f2(S["val_r_psy"]), "ValRhoOB": f2(S["val_rho_ob"]), "ValRhoPsy": f2(S["val_rho_psy"]),
 "ValN": c(S["val_n"]), "ValSumOBN": c(S["val_sum_ob_nppes"]), "ValSumOBA": c(S["val_sum_ob_ahrf"]),
 "ValSumPsyN": c(S["val_sum_psy_nppes"]), "ValSumPsyA": c(S["val_sum_psy_ahrf"]),
 "ValZeroOB": f1(S["val_agree_zero_ob"]), "ValZeroPsy": f1(S["val_agree_zero_psy"]),
 "StateMinPPW": f1(S["state_ppw_per10k_range"][0]), "StateMinPPWst": S["state_ppw_per10k_range"][1],
 "StateMaxPPW": f1(S["state_ppw_per10k_range"][2]), "StateMaxPPWst": S["state_ppw_per10k_range"][3],
 "StateMedPPW": f1(S["state_ppw_per10k_median"]), "NStatesHNLC": c(S["n_states_with_hnlc"]),
 "NVBirths": c(S["nv"]["births"]), "NVNoPPW": c(S["nv"]["n_no_ppw"]), "NVFrontier": c(S["nv"]["n_frontier"]),
 "NVPPW": c(S["nv"]["ppw_total"]), "NVPctBirthsNoPPW": f1(S["nv"]["pct_births_noppw"]), "NVNoOB": c(S["nv"]["n_no_ob"]),
 "NVNoBHP": c(S["nv"]["n_no_bhp"]), "NVCWBirths": f1(S["nv"]["clark_washoe_share_births"]), "NVCWPPW": f1(S["nv"]["clark_washoe_share_ppw"]),
 "ROB": f3(B["r_ob_vs_ahrf"]),
}
for cl in ["metro", "rural", "frontier"]:
    k = cl.capitalize()
    M[f"NoPPW{k}"] = f1(R[cl]["no_ppw"]); M[f"NoBHP{k}"] = f1(R[cl]["no_bhp"]); M[f"NoOB{k}"] = f1(R[cl]["no_ob"])
    M[f"NoHC{k}"] = f1(R[cl]["no_hc"]); M[f"GapMed{k}"] = f1(R[cl]["gap_med"]); M[f"NeedMed{k}"] = f1(R[cl]["need_med"])
    M[f"CapMed{k}"] = f1(R[cl]["cap_med"]); M[f"DepMed{k}"] = f1(R[cl]["dep_med"]); M[f"SVIMed{k}"] = f2(R[cl]["svi_med"])
    M[f"PctBirths{k}"] = f1(R[cl]["pct_births"]); M[f"BirthsNoPPW{k}"] = c(R[cl]["births_no_ppw"])
    M[f"BHPerK{k}"] = f1(R[cl]["bh_per_1k_med"]); M[f"OBPerK{k}"] = f1(R[cl]["ob_per_1k_med"])
top5 = S["states_top5_births_noppw"]
M["TopStates"] = ", ".join(f"{s} ({v:.1f}\\%)" for s, v in top5)
M["ZeroStates"] = ", ".join(S["states_zero_births_noppw"])
M["HNLCStates"] = ", ".join(f"{s} ({v})" for s, v in S["hnlc_states"])
sens = {r["label"]: r for r in S["sensitivity"]}
M["SensRhoMin"] = f3(min(r["rho"] for r in S["sensitivity"])); M["SensJacMin"] = f2(min(r["jaccard"] for r in S["sensitivity"]))
M["SensWomenRho"] = f3(sens["Capacity per 1,000 women aged 15-44"]["rho"]); M["SensWomenStorey"] = f1(sens["Capacity per 1,000 women aged 15-44"]["storey"])
M["SensUnrankedJac"] = f2(sens["Counties with <20 births unranked"]["jaccard"]); M["SensUnrankedN"] = c(sens["Counties with <20 births unranked"]["n_hnlc"])
with open(os.path.join(H, "numbers.tex"), "w") as fh:
    fh.write("% generated by make_tex_inputs.py from paper_stats.json -- do not edit\n")
    for k, v in M.items():
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

# Table: rurality summary
rows = [("Counties", "n", c), ("Births per year", "births", c), ("Share of U.S. births (\\%)", "pct_births", f1),
        ("Women aged 15--44", "women", c), ("Adult depression, median (\\%)", "dep_med", f1), ("SVI overall, median", "svi_med", f2),
        ("No PPW SUD program (\\% of counties)", "no_ppw", f1), ("No behavioral prescriber (\\%)", "no_bhp", f1),
        ("No obstetric clinician (\\%)", "no_ob", f1), ("No health center site (\\%)", "no_hc", f1),
        ("BH clinicians per 1,000 births, median", "bh_per_1k_med", f1), ("Obstetric clinicians per 1,000 births, median", "ob_per_1k_med", f1),
        ("Need score, median", "need_med", f1), ("Capacity score, median", "cap_med", f1), ("Gap score, median", "gap_med", f1),
        ("High need, low capacity (counties)", "hnlc", c)]
L = ["\\begin{tabular}{@{}lrrrr@{}}", "\\toprule", " & Metro & Rural & Frontier & All \\\\", "\\midrule"]
for lab, k, fn in rows:
    L.append(lab + " & " + " & ".join(fn(R[cl][k]).replace("-", "$-$") if k == "gap_med" else fn(R[cl][k]) for cl in ["metro", "rural", "frontier", "all"]) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(os.path.join(H, "tables", "tab_rurality.tex"), "w").write("\n".join(L))

# Table: top 15
t = pd.read_csv(os.path.join(H, "tables", "top15_gap.csv"), dtype={"fips": str})
L = ["\\begin{tabular}{@{}rllrrrrrrrr@{}}", "\\toprule",
     "\\# & County & Class & Births & Dep.\\,\\% & SVI & PPW & BH & OB & Need & Gap \\\\", "\\midrule"]
for i, r in enumerate(t.itertuples(), 1):
    L.append(f"{i} & {r.county_name.replace(' County','').replace(' Parish','')}, {r.state} & {r.rurality_class} & {int(r.births):,} & {r.depression_crude_pct:.1f} & {r.svi_overall:.2f} & {r.ppw_sud_facilities} & {r.bh_clinicians} & {r.ob_clinicians} & {r.need_score:.1f} & +{r.gap_score:.1f} \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(os.path.join(H, "tables", "tab_top15.tex"), "w").write("\n".join(L))

# Table: Nevada
n = pd.read_csv(os.path.join(H, "tables", "nevada.csv"), dtype={"fips": str})
L = ["\\begin{tabular}{@{}llrrrrrrrr@{}}", "\\toprule",
     "County & Class & Births & Dep.\\,\\% & SVI & PPW & HC & OB & BH & Gap \\\\", "\\midrule"]
for r in n.itertuples():
    g = f"{r.gap_score:+.1f}".replace("-", "$-$")
    flag = "$^\\dagger$" if r.births < 20 else ""
    L.append(f"{r.county_name.replace(' County','')}{flag} & {r.rurality_class} & {int(r.births):,} & {r.depression_crude_pct:.1f} & {r.svi_overall:.2f} & {r.ppw_sud_facilities} & {r.hc_sites} & {r.ob_clinicians} & {r.bh_clinicians:,} & {g} \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(os.path.join(H, "tables", "tab_nevada.tex"), "w").write("\n".join(L))

# Table: sensitivity
s = pd.DataFrame(S["sensitivity"])
L = ["\\begin{tabular}{@{}lrrrr@{}}", "\\toprule", "Specification & $\\rho$ & HNLC $n$ & Overlap & Jaccard \\\\", "\\midrule"]
for r in s.itertuples():
    rho = "$>$0.999" if (r.rho >= 0.9995 and r.label != "Baseline") else f"{r.rho:.3f}"
    lab = r.label.replace("<20", "$<$20").replace("15-44", "15--44")
    L.append(f"{lab} & {rho} & {r.n_hnlc} & {r.overlap} & {r.jaccard:.2f} \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(os.path.join(H, "tables", "tab_sensitivity.tex"), "w").write("\n".join(L))
print(len(M), "macros")
