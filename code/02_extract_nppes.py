#!/usr/bin/env python3
"""02_extract_nppes.py: pull perinatal-relevant clinicians out of the NPPES file.

Plain-language summary: the national clinician registry has about 9 million
records. This script keeps only active individual clinicians whose main
specialty is on the list in code/config.py, and writes them to
data/processed/nppes_clinicians.csv with their practice ZIP code. It reads
the file straight from the zip, so it needs no extra disk space. Takes about
10 to 20 minutes. You do not need to open it.

Rules (also in docs/CODING_RULES.md):
- Entity type 1 (individual clinicians) only.
- Active: no deactivation date, or a reactivation date after it.
- Primary taxonomy = the slot with Primary Taxonomy Switch "Y"; if no slot is
  flagged, slot 1. Each NPI counted once, in its primary group.
- Location = primary business practice location (US, 5-digit ZIP).
"""

import glob
import io
import os
import sys
import zipfile

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import PROC, RAW, TAXONOMY_GROUPS  # noqa: E402

CODE2GROUP = {c: g for g, d in TAXONOMY_GROUPS.items() for c in d}
TAX = [f"Healthcare Provider Taxonomy Code_{i}" for i in range(1, 16)]
SW = [f"Healthcare Provider Primary Taxonomy Switch_{i}" for i in range(1, 16)]
COLS = ["NPI", "Entity Type Code", "NPI Deactivation Date", "NPI Reactivation Date",
        "Provider Business Practice Location Address City Name",
        "Provider Business Practice Location Address State Name",
        "Provider Business Practice Location Address Postal Code",
        "Provider Business Practice Location Address Country Code (If outside U.S.)"] + TAX + SW


def main():
    zpath = sorted(glob.glob(os.path.join(RAW, "NPPES_Data_Dissemination_*_V2.zip")))[-1]
    os.makedirs(PROC, exist_ok=True)
    out = []
    stats = {"rows_read": 0, "type1": 0, "type1_active": 0, "kept": 0}
    with zipfile.ZipFile(zpath) as z:
        name = [n for n in z.namelist() if n.startswith("npidata_pfile") and not n.endswith("fileheader.csv")][0]
        with z.open(name) as fh:
            reader = pd.read_csv(io.TextIOWrapper(fh, encoding="utf-8", errors="replace"), usecols=COLS,
                                 dtype=str, chunksize=500_000, keep_default_na=False)
            for i, ch in enumerate(reader):
                stats["rows_read"] += len(ch)
                ch = ch[ch["Entity Type Code"] == "1"]
                stats["type1"] += len(ch)
                deact = pd.to_datetime(ch["NPI Deactivation Date"], errors="coerce")
                react = pd.to_datetime(ch["NPI Reactivation Date"], errors="coerce")
                active = deact.isna() | (react.notna() & (react > deact))
                ch = ch[active]
                stats["type1_active"] += len(ch)
                # primary taxonomy
                tax = ch[TAX].to_numpy()
                sw = ch[SW].to_numpy()
                prim = []
                for t_row, s_row in zip(tax, sw):
                    p = ""
                    for t, s in zip(t_row, s_row):
                        if s == "Y" and t:
                            p = t
                            break
                    prim.append(p or t_row[0])
                ch = ch.assign(primary_taxonomy=prim)
                ch = ch[ch["primary_taxonomy"].isin(CODE2GROUP)]
                ch = ch.assign(group=ch["primary_taxonomy"].map(CODE2GROUP))
                out.append(ch[["NPI", "primary_taxonomy", "group",
                               "Provider Business Practice Location Address City Name",
                               "Provider Business Practice Location Address State Name",
                               "Provider Business Practice Location Address Postal Code",
                               "Provider Business Practice Location Address Country Code (If outside U.S.)"]])
                stats["kept"] += len(ch)
                print(f"  chunk {i + 1}: read {stats['rows_read']:,}, kept {stats['kept']:,}", flush=True)
    df = pd.concat(out, ignore_index=True)
    df.columns = ["npi", "primary_taxonomy", "group", "practice_city", "practice_state", "practice_postal",
                  "practice_country"]
    df["zip5"] = df["practice_postal"].str[:5]
    df.to_csv(os.path.join(PROC, "nppes_clinicians.csv"), index=False)
    with open(os.path.join(PROC, "nppes_extract_stats.txt"), "w") as f:
        f.write(f"source_file={os.path.basename(zpath)}\n")
        for k, v in stats.items():
            f.write(f"{k}={v}\n")
        for g, n in df["group"].value_counts().items():
            f.write(f"group_{g}={n}\n")
    print(stats)


if __name__ == "__main__":
    main()
