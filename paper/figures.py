#!/usr/bin/env python3
"""paper/figures.py: the preprint's figures (Matplotlib + seaborn), from data/processed and paper_stats.json."""
import json, os, sys
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch
import numpy as np, pandas as pd, seaborn as sns

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from config import PROC, RAW  # noqa: E402
FIG = os.path.join(ROOT, "paper", "figures"); os.makedirs(FIG, exist_ok=True)
S = json.load(open(os.path.join(ROOT, "paper", "paper_stats.json")))
d = pd.read_csv(os.path.join(PROC, "panel_county.csv"), dtype={"fips": str})

sns.set_theme(style="ticks", context="paper", font="DejaVu Serif")
plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5, "xtick.labelsize": 7.5,
                     "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "axes.linewidth": 0.8,
                     "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True, "ytick.right": True,
                     "savefig.dpi": 300, "savefig.bbox": "tight", "pdf.fonttype": 42})
CC = {"metro": "#2a78d6", "rural": "#eb6834", "frontier": "#1baf7a"}
LAB = {"metro": "Metro", "rural": "Rural", "frontier": "Frontier"}
BINS = [-101, -45, -25, -10, 10, 25, 45, 101]
DIV = ["#184f95", "#2a78d6", "#9ec5f4", "#f0efec", "#f3b0af", "#e34948", "#a32b2b"]
DLAB = ["$-100$ to $-45$", "$-45$ to $-25$", "$-25$ to $-10$", "$-10$ to $+10$", "$+10$ to $+25$", "$+25$ to $+45$", "$+45$ to $+100$"]

def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".pdf"), dpi=400); fig.savefig(os.path.join(FIG, name + ".png"), dpi=200); plt.close(fig)

# F1 pipeline schematic
def f1():
    fig, ax = plt.subplots(figsize=(7.0, 3.3)); ax.set_xlim(0, 100); ax.set_ylim(0, 50); ax.axis("off")
    def box(x, y, w, h, title, body, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec="#52514e", lw=0.7))
        ax.text(x + w / 2, y + h - 2.2, title, ha="center", va="top", fontsize=7.6, weight="bold")
        ax.text(x + w / 2, y + h - 6.0, body, ha="center", va="top", fontsize=5.6, linespacing=1.3)
    box(1, 27, 23, 21, "Need sources", "AHRF 2024-25 births\n(NCHS natality)\nCensus PEP V2024\n(women 15-44)\nCDC PLACES 2025\nCDC/ATSDR SVI 2022", "#e8f1fc")
    box(1, 1, 23, 22, "Capacity sources", "FindTreatment.gov API\n(51 state queries)\nHRSA health center sites\nCMS NPPES, Nov 2026\nNUCC taxonomy v26.1", "#fdeee7")
    box(27.5, 13, 21, 23, "Geography", "Census V2024 counties\n(3,144; CT regions)\npoint-in-polygon;\nZIP to ZCTA to county;\nstate check; RUCC 2023;\nland area (frontier)", "#f0efec")
    box(52, 27, 21, 21, "Release 1: need", "births, women 15-44,\ndepression, SVI,\nrural/frontier flags,\ndata years,\nsmall-number flags", "#e8f1fc")
    box(52, 1, 21, 22, "Release 2: capacity", "26,642 listings coded;\nhealth center sites;\nclinicians in four\ntaxonomy groups;\ncounty totals", "#fdeee7")
    box(76.5, 13, 22.5, 23, "Release 3: gap", "need percentile score\nminus capacity\npercentile score;\nnational/state ranks;\nhigh-need/low-capacity\nflag", "#e7f6f0")
    kw = dict(arrowstyle="-|>", color="#52514e", lw=0.8, mutation_scale=8)
    for a, b in [((24.6, 37), (27.5, 31)), ((24.6, 12), (27.5, 18)), ((49.2, 31), (52, 37)), ((49.2, 18), (52, 12)), ((73.6, 37), (76.5, 31)), ((73.6, 12), (76.5, 18))]:
        ax.annotate("", b, a, arrowprops=kw)
    save(fig, "fig1_pipeline")

def counties():
    g = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_county_500k.zip')}")[["GEOID", "STATEFP", "geometry"]]
    return g.merge(d, left_on="GEOID", right_on="fips")

# F2 gap map
def f2(g):
    g = g.copy(); g["bin"] = pd.cut(g.gap_score, BINS, labels=False)
    g["c"] = g["bin"].map(lambda b: DIV[int(b)] if pd.notna(b) else "#ffffff")
    fig = plt.figure(figsize=(7.0, 4.4)); ax = fig.add_axes([0, 0.05, 1, 0.95])
    co = g[~g.STATEFP.isin(["02", "15"])].to_crs(5070)
    co.plot(ax=ax, color=co.c, edgecolor="#fcfcfb", linewidth=0.08, rasterized=True); co.dissolve("STATEFP").boundary.plot(ax=ax, color="white", lw=0.45, rasterized=True)
    ax.axis("off")
    a2 = fig.add_axes([0.0, 0.05, 0.22, 0.25]); ak = g[g.STATEFP == "02"].to_crs(3338)
    ak.plot(ax=a2, color=ak.c, edgecolor="#fcfcfb", lw=0.08, rasterized=True); a2.set_xlim(-2.4e6, 1.6e6); a2.axis("off")
    a3 = fig.add_axes([0.22, 0.06, 0.12, 0.12]); hi = g[g.STATEFP == "15"].to_crs(32604)
    hi.plot(ax=a3, color=hi.c, edgecolor="#fcfcfb", lw=0.08, rasterized=True); a3.axis("off")
    fig.legend(handles=[Patch(fc=c, ec="#c3c2b7", lw=0.4, label=l) for c, l in zip(DIV, DLAB)], loc="lower right",
               bbox_to_anchor=(0.995, 0.06), frameon=True, title="Gap score", ncol=1, fontsize=6.8, title_fontsize=7.5)
    save(fig, "fig2_gap_map")

# F3 lacking services by class
def f3():
    R = S["rurality"]; items = [("no_ppw", "PPW SUD\nprogram"), ("no_bhp", "Behavioral\nprescriber"), ("no_ob", "Obstetric\nclinician"), ("no_hc", "Health\ncenter site")]
    fig, ax = plt.subplots(figsize=(3.4, 2.8)); x = np.arange(len(items)); wdt = 0.26
    for i, c in enumerate(["metro", "rural", "frontier"]):
        vals = [R[c][k] for k, _ in items]
        b = ax.bar(x + (i - 1) * wdt, vals, wdt * 0.92, color=CC[c], label=f"{LAB[c]} ($n$={int(R[c]['n']):,})")
        for xi, v in zip(x + (i - 1) * wdt, vals):
            ax.text(xi, v + 1.2, f"{v:.0f}", ha="center", fontsize=5.6)
    ax.set_xticks(x, [l for _, l in items], fontsize=6.6); ax.set_ylabel("Counties with none in county (%)"); ax.set_ylim(0, 100)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=6.0, handlelength=1.0, columnspacing=0.8); ax.grid(axis="y", color="#e1e0d9", lw=0.5); ax.set_axisbelow(True)
    save(fig, "fig3_lacking_by_class")

# F4 need vs capacity
def f4():
    fig, ax = plt.subplots(figsize=(3.4, 3.1))
    for c in ["metro", "rural", "frontier"]:
        s = d[d.rurality_class == c]
        ax.scatter(s.capacity_score, s.need_score, s=4, alpha=0.55, color=CC[c], lw=0, label=LAB[c])
    qn, qc = d.need_score.quantile(.75), d.capacity_score.quantile(.25)
    ax.axhline(qn, color="#52514e", lw=0.7, ls="--"); ax.axvline(qc, color="#52514e", lw=0.7, ls="--")
    ax.fill_between([0, qc], qn, 100, color="#e34948", alpha=0.08, lw=0)
    ax.text(1.5, 98, f"high need,\nlow capacity\n($n$={S['base']['n_high_need_low_capacity']})", va="top", fontsize=6.3)
    ax.plot([0, 100], [0, 100], color="#898781", lw=0.6)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.set_xlabel("Capacity score (percentile)"); ax.set_ylabel("Need score (percentile)")
    ax.legend(loc="lower right", markerscale=3, frameon=True)
    save(fig, "fig4_need_vs_capacity")

# F5 states
def f5():
    st = pd.read_csv(os.path.join(ROOT, "paper", "tables", "state_summary.csv")).sort_values("pct_births_noppw")
    fig, ax = plt.subplots(figsize=(3.4, 6.4))
    cols = ["#e34948" if s == "NV" else "#2a78d6" for s in st.state]
    ax.barh(st.state, st.pct_births_noppw, color=cols, height=0.72)
    ax.set_xlabel("Births in counties with no PPW SUD program (%)"); ax.set_ylim(-0.7, len(st) - 0.3)
    ax.tick_params(axis="y", labelsize=6); ax.grid(axis="x", color="#e1e0d9", lw=0.5); ax.set_axisbelow(True)
    ax.axvline(S["base"]["pct_births_in_no_ppw_counties"], color="#52514e", ls="--", lw=0.7)
    ax.text(S["base"]["pct_births_in_no_ppw_counties"] + 1, 1.5, f"U.S. {S['base']['pct_births_in_no_ppw_counties']}%", fontsize=6.3)
    save(fig, "fig5_states")

# F6 validation
def f6():
    v = pd.read_csv(os.path.join(ROOT, "paper", "validation_ahrf.csv"))
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for ax, (x, y, xl, yl, r) in zip(axs, [("ahrf_ob", "ob_clinicians", "AHRF OB/GYN physicians, 2023", "NPPES obstetric clinicians, 2026", S["val_r_ob"]),
                                          ("ahrf_psy", "bh_prescribers", "AHRF psychiatrists, 2023", "NPPES behavioral prescribers, 2026", S["val_r_psy"])]):
        for c in ["metro", "rural", "frontier"]:
            s = v[v.rurality_class == c]
            ax.scatter(s[x] + 1, s[y] + 1, s=4, alpha=0.5, lw=0, color=CC[c], label=LAB[c])
        ax.set_xscale("log"); ax.set_yscale("log"); lim = [0.8, 2e4]; ax.plot(lim, lim, color="#52514e", lw=0.7, ls="--")
        ax.set_xlim(lim); ax.set_ylim(lim); ax.set_xlabel(xl + " (+1)"); ax.set_ylabel(yl + " (+1)")
        ax.text(1.1, 9e3, f"$r$ (log) = {r:.2f}\n$n$ = {S['val_n']:,}", fontsize=7, va="top")
    axs[1].legend(loc="lower right", markerscale=3, frameon=True)
    fig.tight_layout(); save(fig, "fig6_validation")

# F7 small counties
def f7():
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    for c in ["metro", "rural", "frontier"]:
        s = d[(d.rurality_class == c) & (d.births > 0)]
        ax.scatter(s.births, s.capacity_score, s=4, alpha=0.5, lw=0, color=CC[c], label=LAB[c])
    ax.set_xscale("log"); ax.axvline(20, color="#52514e", ls="--", lw=0.7)
    ax.text(21, 4, "20 births", fontsize=6.3)
    stv = d[d.fips == "32029"].iloc[0]
    ax.annotate("Storey, NV", (stv.births, stv.capacity_score), xytext=(60, 92), fontsize=6.5,
                arrowprops=dict(arrowstyle="-", color="#52514e", lw=0.6))
    ax.set_xlabel("Annual births (log scale)"); ax.set_ylabel("Capacity score (percentile)"); ax.set_ylim(0, 100)
    ax.legend(loc="lower right", markerscale=3, frameon=True)
    save(fig, "fig7_small_counties")

# F8 Nevada
def f8(g):
    nv = g[g.STATEFP == "32"].to_crs(32611).copy(); nv["bin"] = pd.cut(nv.gap_score, BINS, labels=False)
    nv["c"] = nv["bin"].map(lambda b: DIV[int(b)])
    fig, ax = plt.subplots(figsize=(3.4, 4.4)); nv.plot(ax=ax, color=nv.c, edgecolor="white", lw=0.9)
    xmin, ymin, xmax, ymax = nv.total_bounds; small = {"Storey County": 0, "Carson City": 1, "Lyon County": 2, "Douglas County": 3}
    for _, r in nv.iterrows():
        p = r.geometry.representative_point(); nm = r.county_name.replace(" County", "")
        t = f"{nm}\n{r.gap_score:+.0f} | {r.ppw_sud_facilities}"
        if r.county_name in small:
            ty = ymax - (0.47 + 0.09 * small[r.county_name]) * (ymax - ymin)
            ax.annotate(t, (p.x, p.y), xytext=(xmin - 0.40 * (xmax - xmin), ty), fontsize=5.4, va="center",
                        arrowprops=dict(arrowstyle="-", color="#898781", lw=0.5))
        else:
            dy = {"Eureka County": -0.10, "Lander County": 0.06}.get(r.county_name, 0) * (ymax - ymin)
            ax.text(p.x, p.y + dy, t, ha="center", va="center", fontsize=5.4)
    ax.set_xlim(xmin - 0.42 * (xmax - xmin), xmax + 0.02 * (xmax - xmin)); ax.axis("off")
    ax.legend(handles=[Patch(fc=c, ec="#c3c2b7", lw=0.4, label=l) for c, l in zip(DIV, DLAB)], loc="upper center",
              fontsize=5.2, title="Gap score", title_fontsize=6, frameon=False, bbox_to_anchor=(0.5, 0.0), ncol=4,
              handlelength=1.0, columnspacing=0.7)
    save(fig, "fig8_nevada")

# F9 sensitivity
def f9():
    s = pd.DataFrame(S["sensitivity"]).iloc[1:][::-1]
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True, gridspec_kw={"wspace": 0.08})
    axs[0].scatter(s.rho, s.label, color="#2a78d6", s=18, zorder=3); axs[0].set_xlim(0.95, 1.002)
    axs[0].set_xlabel("Spearman $\\rho$ with baseline gap")
    axs[1].barh(s.label, s.jaccard, color="#eb6834", height=0.55); axs[1].set_xlim(0, 1)
    axs[1].set_xlabel("Jaccard overlap, high-need/low-capacity set")
    for ax in axs:
        ax.grid(axis="x", color="#e1e0d9", lw=0.5); ax.set_axisbelow(True)
    save(fig, "fig9_sensitivity")

if __name__ == "__main__":
    g = counties(); f1(); f2(g); f3(); f4(); f5(); f6(); f7(); f8(g); f9(); print("ok")
