#!/usr/bin/env python3
"""Turn paper/main.tex into a pandoc-friendly LaTeX file for the Word manuscript.
Resolves figure/table/section/citation numbers from main.aux so Word matches the PDF."""
import os, re
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tex = open(os.path.join(H, "main.tex")).read()
aux = open(os.path.join(H, "main.aux")).read()
labels = {m.group(1): m.group(2) for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux)}
cites = {m.group(1): int(m.group(2)) for m in re.finditer(r"\\bibcite\{([^}]+)\}\{\{(\d+)\}", aux)}
macros = {m.group(1): m.group(2) for m in re.finditer(r"\\newcommand\{\\(\w+)\}\{(.*)\}", open(os.path.join(H, "numbers.tex")).read())}

def compress(nums):
    nums = sorted(set(nums)); out = []; i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1: j += 1
        out.append(f"{nums[i]}--{nums[j]}" if j - i >= 2 else ", ".join(map(str, nums[i:j + 1])))
        i = j + 1
    return "[" + ", ".join(out) + "]"

def expand(s):
    for _ in range(3):
        s = re.sub(r"\\(\w+)(?![a-zA-Z])", lambda m: macros.get(m.group(1), m.group(0)), s)
    return s

# header
abstract = re.search(r"\\begin\{minipage\}\{0.80\\textwidth\}\s*\\small\s*(.*?)\\par\s*\\vspace\{4pt\}", tex, re.S).group(1)
keywords = re.search(r"\\textbf\{Keywords:\}(.*?)\n\\end\{minipage\}", tex, re.S).group(1).strip()
body = tex[tex.index("\\section{Introduction}"):tex.index("\\end{thebibliography}") + len("\\end{thebibliography}")]

s = body
s = s.replace("\\FloatBarrier\n", "")
s = re.sub(r"\\resizebox\{[^}]*\}\{!\}\{(\\input\{[^}]*\})\}", r"\1", s)
s = re.sub(r"\\setlength\{\\tabcolsep\}\{[^}]*\}\n", "", s)
s = re.sub(r"\\(scriptsize|footnotesize|small)\n", "", s)
s = s.replace("\\begin{figure*}", "\\begin{figure}").replace("\\end{figure*}", "\\end{figure}")
s = s.replace("\\begin{table*}", "\\begin{table}").replace("\\end{table*}", "\\end{table}")
s = re.sub(r"\\begin\{(figure|table)\}\[[^\]]*\]", r"\\begin{\1}", s)
s = re.sub(r"\\includegraphics\[([^\]]*)\]\{figures/([^}]+)\.pdf\}",
           lambda m: "\\includegraphics[width=" + ("3.9in" if "columnwidth" in m.group(1) else "6.4in") + "]{figures/" + m.group(2) + ".png}", s)
# inline the tables (pandoc reads \input, but expand macros inside them too)
s = re.sub(r"\\input\{([^}]+)\}", lambda m: open(os.path.join(H, m.group(1) if m.group(1).endswith(".tex") else m.group(1) + ".tex")).read(), s)
# captions with labels -> numbered captions
def cap(m):
    env_body = m.group(0)
    lab = re.search(r"\\label\{([^}]+)\}", env_body)
    if not lab: return env_body
    num = labels[lab.group(1)]
    kind = "Figure" if lab.group(1).startswith("fig") else "Table"
    env_body = re.sub(r"\\caption\{", lambda _: "\\caption{" + f"\\textbf{{{kind} {num}.}} ", env_body, count=1)
    return env_body
s = re.sub(r"\\begin\{(figure|table)\}.*?\\end\{\1\}", cap, s, flags=re.S)
# refs and cites
s = re.sub(r"\\ref\{([^}]+)\}", lambda m: labels.get(m.group(1), "?"), s)
s = re.sub(r"\\cite\{([^}]+)\}", lambda m: compress([cites[k.strip()] for k in m.group(1).split(",")]), s)
s = s.replace("Fig.~", "Figure~").replace("Table~", "Table~")
s = re.sub(r"\\label\{[^}]+\}", "", s)
# section numbering prefixes (Roman sections, lettered subsections) to match the PDF
sec = 0; sub = 0; sss = 0; out = []
for line in s.split("\n"):
    m = re.match(r"\\(section|subsection|subsubsection)(\*?)\{(.*)\}(.*)$", line)
    if m and not m.group(2):
        kind, title, rest = m.group(1), m.group(3), m.group(4)
        if kind == "section":
            sec += 1; sub = 0
            romans = "I II III IV V VI VII VIII".split()
            line = f"\\section*{{{romans[sec-1]}. {title}}}{rest}"
        elif kind == "subsection":
            sub += 1; sss = 0
            line = f"\\subsection*{{{chr(64+sub)}. {title}}}{rest}"
        else:
            sss += 1
            line = f"\\textit{{{sss}. {title}.}} {rest}"
    out.append(line)
s = "\n".join(out)
# bibliography -> numbered paragraphs
def bib(m):
    items = re.findall(r"\\bibitem\{([^}]+)\}\s*(.*?)(?=\\bibitem|\\end\{thebibliography\})", m.group(0), re.S)
    return "\\section*{References}\n\n" + "\n\n".join(f"[{cites[k]}] {v.strip()}" for k, v in items)
s = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", bib, s, flags=re.S)
s = s.replace("\\noindent ", "")
s = expand(s).replace("{,}", ",")
abstract = expand(abstract).replace("{,}", ",")

head = r"""\documentclass{article}
\usepackage{amsmath}\usepackage{graphicx}\usepackage{booktabs}
\begin{document}
""" + r"""\begin{center}
\textbf{Where Perinatal Behavioral Health Need Outpaces Treatment Capacity: An Open County-Level Need and Capacity Panel for the United States}
\end{center}

\begin{center}
Munachimso A. Emesobum$^{1,*}$
\end{center}

$^{1}$ Independent Researcher, Nevada, USA

$^{*}$ Correspondence: emesobumm@gmail.com; ORCID: https://orcid.org/0009-0002-7506-2153

\textbf{Abstract:} """ + abstract.strip() + "\n\n\\textbf{Keywords:} " + keywords + "\n\n"
open(os.path.join(H, "word", "manuscript_for_pandoc.tex"), "w").write(head + s + "\n\\end{document}\n")
print("ok", len(s))

# ---- inline math -> Unicode text (portable across Word, LibreOffice, and the preprints.org HTML converter)
SUP = str.maketrans("0123456789-+,*", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺˒*")
SUB = str.maketrans("0123456789ik", "₀₁₂₃₄₅₆₇₈₉ᵢₖ")
def uni(m):
    t = m.group(1)
    t = t.replace("\\rho", "ρ").replace("\\geq", " ≥ ").replace("\\chi", "χ").replace("\\in", " ∈ ").replace("\\dagger", "†")
    t = t.replace("\\times", " × ").replace("\\,", "").replace("\\mathrm{GFR}", "GFR").replace("\\sum", "Σ")
    t = re.sub(r"\^\{([^}]*)\}", lambda k: k.group(1).translate(SUP), t)
    t = re.sub(r"\^(\S)", lambda k: k.group(1).translate(SUP), t)
    t = re.sub(r"_\{([^}]*)\}", lambda k: k.group(1).translate(SUB), t)
    t = re.sub(r"_(\S)", lambda k: k.group(1).translate(SUB), t)
    t = re.sub(r"\s*([=<>])\s*", r" \1 ", t).replace("  ", " ")
    return t.strip() if t.strip() not in ("-",) else "−"
full = open(os.path.join(H, "word", "manuscript_for_pandoc.tex")).read()
pre, post = full.split("\\begin{align}", 1); mid, rest = post.split("\\end{align}", 1)
conv = lambda x: re.sub(r"(?<!\\)\$([^$]+?)(?<!\\)\$", uni, x.replace("\\$", "USDSIGN")).replace("USDSIGN", "\\$")
full = conv(pre) + "\\begin{align}" + mid + "\\end{align}" + conv(rest)
open(os.path.join(H, "word", "manuscript_for_pandoc.tex"), "w").write(full)
