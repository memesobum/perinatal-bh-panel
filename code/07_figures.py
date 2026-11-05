#!/usr/bin/env python3
"""07_figures.py: maps and charts, built from data/processed and report/stats.json.

Plain-language summary: draws three figures into report/figures/. Every figure
carries a DRAFT stamp until the verification gate passes; then run with --final.
  fig1_gap_map_national.png    gap score for every county
  fig2_no_ppw_by_rurality.png  share of counties with no pregnant/postpartum SUD listing
  fig3_nevada_gap.png          Nevada close-up for checking against your county maps
Colors: diverging blue (capacity ranks above need) to red (need ranks above capacity),
gray midpoint; palette from the dataviz skill reference instance.
"""

import argparse
import json
import os
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from config import DRAFT, PROC, RAW, REPORT  # noqa: E402

FIG = os.path.join(REPORT, "figures")
INK, INK2, MUTED, SURF, EDGE = "#0b0b0b", "#52514e", "#898781", "#fcfcfb", "#c3c2b7"
BINS = [-101, -45, -25, -10, 10, 25, 45, 101]
COLORS = ["#184f95", "#2a78d6", "#9ec5f4", "#f0efec", "#f3b0af", "#e34948", "#a32b2b"]
LABELS = ["-100 to -45", "-45 to -25", "-25 to -10", "-10 to +10", "+10 to +25", "+25 to +45", "+45 to +100"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK,
                     "axes.edgecolor": EDGE, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED})


def stamp(fig, final):
    if not final:
        fig.text(0.99, 0.01, "DRAFT - not verified", ha="right", va="bottom", fontsize=11, color="#d03b3b",
                 fontweight="bold")


def load():
    g = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_county_500k.zip')}")[["GEOID", "STATEFP", "geometry"]]
    d = pd.read_csv(os.path.join(PROC, "panel_county.csv"), dtype={"fips": str})
    g = g.merge(d, left_on="GEOID", right_on="fips", how="inner")
    g["bin"] = pd.cut(g.gap_score, BINS, labels=False)
    g["color"] = g["bin"].map(lambda b: COLORS[int(b)] if pd.notna(b) else "#ffffff")
    return g


def fig1(g, final):
    fig = plt.figure(figsize=(11, 7), facecolor=SURF)
    ax = fig.add_axes([0.0, 0.08, 1.0, 0.80])
    cont = g[~g.STATEFP.isin(["02", "15"])].to_crs(5070)
    cont.plot(ax=ax, color=cont.color, edgecolor=SURF, linewidth=0.15)
    states = cont.dissolve("STATEFP")
    states.boundary.plot(ax=ax, color="#ffffff", linewidth=0.6)
    ax.set_axis_off()
    ax_ak = fig.add_axes([0.02, 0.08, 0.20, 0.22])
    ak = g[g.STATEFP == "02"].to_crs(3338)
    ak.plot(ax=ax_ak, color=ak.color, edgecolor=SURF, linewidth=0.15)
    ax_ak.set_xlim(-2.4e6, 1.6e6)
    ax_ak.set_axis_off()
    ax_hi = fig.add_axes([0.22, 0.08, 0.12, 0.12])
    hi = g[g.STATEFP == "15"].to_crs(32604)
    hi.plot(ax=ax_hi, color=hi.color, edgecolor=SURF, linewidth=0.15)
    ax_hi.set_axis_off()
    fig.text(0.02, 0.95, "Where perinatal behavioral health need ranks above treatment capacity",
             fontsize=15, fontweight="bold")
    fig.text(0.02, 0.915, "Gap score by county: need percentile minus capacity percentile. Red = need ranks higher "
             "than capacity; blue = capacity ranks higher.", fontsize=10, color=INK2)
    handles = [Patch(facecolor=c, edgecolor=EDGE, linewidth=0.4, label=l) for c, l in zip(COLORS, LABELS)]
    fig.legend(handles=handles, loc="lower right", bbox_to_anchor=(0.98, 0.12), frameon=False, fontsize=8.5,
               title="Gap score", title_fontsize=9)
    fig.text(0.02, 0.04, "Sources: AHRF 2024-2025; Census PEP V2024; CDC PLACES 2025 (KY, PA from 2024 release); "
             "CDC/ATSDR SVI 2022;", fontsize=7, color=MUTED)
    fig.text(0.02, 0.02, "FindTreatment.gov (accessed 2026-11-04); HRSA health center sites; NPPES Nov 2026. "
             "Counties with fewer than 20 births are unstable; see flags in the data.", fontsize=7, color=MUTED)
    stamp(fig, final)
    fig.savefig(os.path.join(FIG, "fig1_gap_map_national.png"), dpi=200, facecolor=SURF)
    plt.close(fig)


def fig2(final):
    st = json.load(open(os.path.join(REPORT, "stats.json")))
    order = ["metro", "rural", "frontier"]
    vals = [st["pct_no_ppw_by_class"][k] for k in order]
    ns = [st["n_metro"], st["n_rural"], st["n_frontier"]]
    fig, ax = plt.subplots(figsize=(8.5, 4.4), facecolor=SURF)
    ax.set_facecolor(SURF)
    bars = ax.bar([f"{k.capitalize()}\n({n:,} counties)" for k, n in zip(order, ns)], vals, color="#2a78d6",
                  width=0.55, edgecolor=SURF, linewidth=2)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%", ha="center", fontsize=11, color=INK)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percent of counties")
    ax.yaxis.grid(True, color="#e1e0d9", linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    fig.suptitle("Counties with no substance use treatment listing\nfor pregnant or postpartum women",
                 x=0.02, ha="left", fontsize=11.5, fontweight="bold")
    fig.text(0.02, 0.81, "FindTreatment.gov listings coded 'Pregnant/postpartum women', accessed 2026-11-04. "
             "Frontier = under 6 people per sq mi.", fontsize=8, color=INK2)
    fig.subplots_adjust(top=0.74, bottom=0.18)
    stamp(fig, final)
    fig.savefig(os.path.join(FIG, "fig2_no_ppw_by_rurality.png"), dpi=200, facecolor=SURF)
    plt.close(fig)


def fig3(g, final):
    nv = g[g.STATEFP == "32"].to_crs(32611)
    fig, ax = plt.subplots(figsize=(7.5, 9), facecolor=SURF)
    nv.plot(ax=ax, color=nv.color, edgecolor="#ffffff", linewidth=1.2)
    small = {"Storey County": 0, "Carson City": 1, "Lyon County": 2, "Douglas County": 3}
    xmin, ymin, xmax, ymax = nv.total_bounds
    for _, r in nv.iterrows():
        p = r.geometry.representative_point()
        name = r.county_name.replace(" County", "")
        txt = f"{name}\n{r.rurality_class}\ngap {r.gap_score:+.0f}\nPPW SUD sites {r.ppw_sud_facilities}"
        if r.county_name in small:
            ty = ymax - (0.42 + 0.11 * small[r.county_name]) * (ymax - ymin)
            ax.annotate(txt, (p.x, p.y), xytext=(xmin - 0.30 * (xmax - xmin), ty), ha="left", va="center",
                        fontsize=6.8, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
        else:
            dy = {"Eureka County": -0.10, "Lander County": 0.06}.get(r.county_name, 0) * (ymax - ymin)
            ax.annotate(txt, (p.x, p.y + dy), ha="center", va="center", fontsize=6.8, color=INK)
    ax.set_xlim(xmin - 0.32 * (xmax - xmin), xmax + 0.02 * (xmax - xmin))
    ax.set_axis_off()
    handles = [Patch(facecolor=c, edgecolor=EDGE, linewidth=0.4, label=l) for c, l in zip(COLORS, LABELS)]
    ax.legend(handles=handles, loc="lower left", frameon=False, fontsize=7.5, title="Gap score", title_fontsize=8)
    fig.suptitle("Nevada: perinatal behavioral health gap score by county", x=0.03, ha="left", fontsize=13,
                 fontweight="bold")
    fig.text(0.03, 0.935, "Check against your Larson Institute county maps. Esmeralda, Eureka, and Storey have fewer "
             "than 20 births a year.", fontsize=8, color=INK2)
    stamp(fig, final)
    fig.savefig(os.path.join(FIG, "fig3_nevada_gap.png"), dpi=200, facecolor=SURF)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="remove draft stamps (only after verification)")
    a = ap.parse_args()
    a.final = a.final or not DRAFT
    os.makedirs(FIG, exist_ok=True)
    g = load()
    fig1(g, a.final)
    fig2(a.final)
    fig3(g, a.final)
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
