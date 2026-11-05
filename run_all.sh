#!/usr/bin/env bash
# Rebuild the whole panel from scratch, in order. About 15 to 25 minutes, mostly the NPPES download.
# Building an unverified new version? Run: PANEL_DRAFT=1 bash run_all.sh   (adds draft stamps)
set -euo pipefail
cd "$(dirname "$0")"
python3 code/01_fetch.py
python3 code/02_extract_nppes.py
python3 code/03_build_need.py
python3 code/04_build_capacity.py
python3 code/05_build_gap.py
python3 code/06_qa.py > /dev/null
python3 code/07_figures.py
python3 code/08_package.py
echo "Done. Read data/processed/qa_report.txt first."
