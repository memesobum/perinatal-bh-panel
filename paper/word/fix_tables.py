"""Post-process the pandoc docx: full-width tables with content-proportional columns, 8.5 pt table text,
bold header row, centered figures, letter page with 1-inch margins."""
import sys
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
d = Document(sys.argv[1])
for sec in d.sections:
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for a in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, a, Inches(1))
TW = 6.5
for t in d.tables:
    ncol = len(t.columns)
    lens = [max(1, max((min(len(c.text), 60) for c in col.cells), default=1)) for col in t.columns]
    # wrap long text columns: cap share, give short numeric columns a floor
    w = [max(3.2, l) for l in lens]; tot = sum(w)
    widths = [max(0.5, TW * x / tot) for x in w]; sc = TW / sum(widths); widths = [x * sc for x in widths]
    tblPr = t._tbl.tblPr
    for el in tblPr.findall(qn("w:tblW")): tblPr.remove(el)
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), str(int(TW * 1440))); tw.set(qn("w:type"), "dxa"); tblPr.append(tw)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    grid = t._tbl.tblGrid
    for gc, wi in zip(grid.findall(qn("w:gridCol")), widths): gc.set(qn("w:w"), str(int(wi * 1440)))
    for ri, row in enumerate(t.rows):
        for ci, cell in enumerate(row.cells):
            if ci < len(widths): cell.width = Inches(widths[ci])
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0); p.paragraph_format.space_before = Pt(0)
                for r in p.runs:
                    r.font.size = Pt(8.5)
                    if ri == 0: r.font.bold = True
for p in d.paragraphs:
    if p._p.xpath(".//w:drawing"):
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
from docx.shared import RGBColor
for st in d.styles:
    if st.name.startswith("Heading") or st.name in ("Title", "Subtitle"):
        try:
            st.font.color.rgb = RGBColor(0, 0, 0); st.font.name = "Palatino Linotype"
        except Exception: pass
d.save(sys.argv[2])
print(len(d.tables), "tables")
