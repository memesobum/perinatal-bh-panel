# Preprint

*Plain-language summary: this folder builds the preprint describing the panel. Every number in the paper comes from `paper_stats.json`, which `analysis.py` computes from the released data; nothing is typed by hand.*

Build, in order (from the repository root, after `bash run_all.sh`):

```
python3 paper/analysis.py          # statistics, tests, sensitivity analyses -> paper_stats.json, tables/*.csv
python3 paper/figures.py           # Matplotlib/seaborn figures -> figures/*.pdf, *.png
python3 paper/make_tex_inputs.py   # numbers.tex and tables/*.tex from paper_stats.json
cd paper && latexmk -pdf main.tex  # -> main.pdf
```
