#!/usr/bin/env python3
"""05_build_gap.py: build need-to-capacity gap scores (Release 3).

Plain-language summary: for each county, ranks need and capacity against all
other U.S. counties (0 to 100), then subtracts. A positive gap means need ranks
higher than capacity. Writes data/processed/gap_county.csv and the combined
data/processed/panel_county.csv (need + capacity + gap in one table).

Method (DECISION 4, code/config.py):
  need_score     = mean percentile rank of NEED_COMPONENTS (higher = more need)
  capacity_score = mean percentile rank of CAPACITY_COMPONENTS (higher = more capacity)
  gap_score      = need_score - capacity_score   (range -100 to +100)
Percentile rank = 100 x (rank / number of counties with a value), ties averaged.
A county missing a component is scored on the components it has; the count used is recorded.
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import CAPACITY_COMPONENTS, MIN_BIRTHS_TO_RANK, NEED_COMPONENTS, PROC, SMALL_N  # noqa: E402


def pct_rank(s):
    return (100 * s.rank(method="average", pct=True)).round(1)


def main():
    need = pd.read_csv(os.path.join(PROC, "need_county.csv"), dtype={"fips": str, "state_fips": str})
    cap = pd.read_csv(os.path.join(PROC, "capacity_county.csv"), dtype={"fips": str})
    d = need.merge(cap.drop(columns=["state", "county_name"]), on="fips", how="left", validate="1:1")

    d["ranked"] = (d.births >= MIN_BIRTHS_TO_RANK).astype(int) if MIN_BIRTHS_TO_RANK > 0 else 1
    elig = d.ranked == 1
    for c in NEED_COMPONENTS + CAPACITY_COMPONENTS:
        d[f"pr_{c}"] = pct_rank(d[c].where(elig))
    npr = [f"pr_{c}" for c in NEED_COMPONENTS]
    cpr = [f"pr_{c}" for c in CAPACITY_COMPONENTS]
    d["need_score"] = d[npr].mean(axis=1).round(1)
    d["need_components_n"] = d[npr].notna().sum(axis=1)
    d["capacity_score"] = d[cpr].mean(axis=1).round(1)
    d["capacity_components_n"] = d[cpr].notna().sum(axis=1)
    d["gap_score"] = (d.need_score - d.capacity_score).round(1)
    d["gap_rank_national"] = d.gap_score.rank(ascending=False, method="min").astype("Int64")
    d["gap_rank_in_state"] = d.groupby("state").gap_score.rank(ascending=False, method="min").astype("Int64")
    d["high_need_low_capacity"] = ((d.need_score >= d.need_score.quantile(0.75))
                                   & (d.capacity_score <= d.capacity_score.quantile(0.25))).astype(int)
    d["flag_gap_small_births"] = (d.births < SMALL_N).astype(int)

    gap_cols = ["fips", "state", "county_name", "rurality_class", "rural", "frontier", "births",
                "flag_small_births", "ranked"] + npr + ["need_score", "need_components_n"] + cpr + [
        "capacity_score", "capacity_components_n", "gap_score", "gap_rank_national", "gap_rank_in_state",
        "high_need_low_capacity", "no_ppw_sud_facility", "no_bh_prescriber", "no_ob_clinician"]
    d[gap_cols].to_csv(os.path.join(PROC, "gap_county.csv"), index=False)
    d.to_csv(os.path.join(PROC, "panel_county.csv"), index=False)
    print(d[["need_score", "capacity_score", "gap_score"]].describe().round(1))
    print(d.groupby("rurality_class")[["gap_score", "no_ppw_sud_facility"]].mean().round(2))


if __name__ == "__main__":
    main()
