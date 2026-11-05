"""Graphic abstract for preprints.org (PNG, 2400x1200 px). Numbers from paper_stats.json."""
import json, os, sys
import geopandas as gpd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H)
sys.path.insert(0, os.path.join(ROOT, "code")); from config import PROC, RAW
S = json.load(open(os.path.join(H, "paper_stats.json"))); B = S["base"]; R = S["rurality"]
d = pd.read_csv(os.path.join(PROC, "panel_county.csv"), dtype={"fips": str})
g = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_county_500k.zip')}")[["GEOID", "STATEFP", "geometry"]].merge(d, left_on="GEOID", right_on="fips")
BINS = [-101, -45, -25, -10, 10, 25, 45, 101]; DIV = ["#184f95", "#2a78d6", "#9ec5f4", "#f0efec", "#f3b0af", "#e34948", "#a32b2b"]
g["c"] = pd.cut(g.gap_score, BINS, labels=False).map(lambda b: DIV[int(b)] if pd.notna(b) else "#fff")
plt.rcParams["font.family"] = "DejaVu Serif"
fig = plt.figure(figsize=(12, 6), dpi=200, facecolor="white")
fig.text(0.03, 0.93, "Where perinatal behavioral health need outpaces treatment capacity", fontsize=19, weight="bold", color="#0b0b0b")
fig.text(0.03, 0.885, "An open, versioned county panel for all 3,144 U.S. counties, built only from federal open data", fontsize=12, color="#52514e")
ax = fig.add_axes([0.0, 0.10, 0.60, 0.74])
co = g[~g.STATEFP.isin(["02", "15", "72"])].to_crs(5070)
co.plot(ax=ax, color=co.c, edgecolor="white", linewidth=0.05, rasterized=True); ax.axis("off")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc=DIV[0], label="Capacity ranks above need"), Patch(fc=DIV[3], label="Balanced"), Patch(fc=DIV[6], label="Need ranks above capacity")],
          loc="lower left", frameon=False, fontsize=9.5, bbox_to_anchor=(0.02, -0.02), ncol=3, handlelength=1.2)
x0 = 0.62
def stat(y, big, small, col):
    fig.text(x0, y, big, fontsize=30, weight="bold", color=col)
    fig.text(x0, y - 0.055, small, fontsize=11, color="#0b0b0b", va="top", linespacing=1.35)
stat(0.74, f"{B['pct_no_ppw_sud_facility']:.0f}% of counties", f"have no substance use treatment program\nfor pregnant or postpartum women\n({B['pct_births_in_no_ppw_counties']:.1f}% of U.S. births)", "#a32b2b")
stat(0.50, f"{R['metro']['no_ppw']:.0f}% → {R['rural']['no_ppw']:.0f}% → {R['frontier']['no_ppw']:.0f}%", "of metro, rural, and frontier counties lack\nsuch a program", "#eb6834")
stat(0.27, f"{B['n_high_need_low_capacity']} counties", f"combine top-quartile need with bottom-quartile\ncapacity ({B['high_need_low_capacity_by_class']['rural']} rural, {B['high_need_low_capacity_by_class']['frontier']} frontier)", "#184f95")
fig.text(0.03, 0.058, "Need: births (NCHS), women 15-44, adult depression (CDC PLACES), social vulnerability (CDC/ATSDR SVI).", fontsize=9, color="#52514e")
fig.text(0.03, 0.033, "Capacity: SAMHSA FindTreatment.gov, HRSA health centers, CMS NPPES clinicians. Contiguous U.S. shown; panel covers all 50 states and DC.", fontsize=9, color="#52514e")
fig.text(0.03, 0.008, "Emesobum, M. A. (2026). github.com/memesobum/perinatal-bh-panel", fontsize=9, color="#52514e")
fig.savefig(os.path.join(H, "submission", "Graphic_Abstract.png"), dpi=200, facecolor="white")
print("ok")
