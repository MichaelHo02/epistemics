"""Fill the Apart Research docx template from report.md. Usage: python3 docx_fill.py TEMPLATE.docx OUT.docx"""
import re, sys, zipfile, shutil, os, struct, html
tpl, out = sys.argv[1], sys.argv[2]
W = "tmp_docx"; shutil.rmtree(W, ignore_errors=True); zipfile.ZipFile(tpl).extractall(W)
x = open(f"{W}/word/document.xml", encoding="utf8").read()
md = open("report.md", encoding="utf8").read()
RF = '<w:rFonts w:ascii="Old Standard TT" w:cs="Old Standard TT" w:eastAsia="Old Standard TT" w:hAnsi="Old Standard TT"/>'
esc = lambda t: html.escape(t, quote=False)

def runs(text, sz=None, base_b=False, base_i=False):
    sz_x = f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>' if sz else ""
    out = []
    for tok in re.split(r"(\*\*.+?\*\*|`.+?`|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*]))", text):
        if not tok: continue
        b, i, code = base_b, base_i, False
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4: tok, b = tok[2:-2], True
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2: tok, code = tok[1:-1], True
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2: tok, i = tok[1:-1], True
        font = '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>' if code else RF
        out.append(f'<w:r><w:rPr>{font}{"<w:b/>" if b else ""}{"<w:i/>" if i else ""}{sz_x}</w:rPr><w:t xml:space="preserve">{esc(tok)}</w:t></w:r>')
    return "".join(out)

def para(text, jc=None, sz=None, ind=None, after=120, num=None, keep=False, b=False, i=False):
    ppr = ""
    if keep: ppr += "<w:keepNext/>"
    if num: ppr += f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num}"/></w:numPr>'
    ppr += f'<w:spacing w:after="{after}" w:line="252" w:lineRule="auto"/>'
    if num: ppr += '<w:ind w:left="720" w:hanging="360"/>'
    elif ind: ppr += f'<w:ind w:left="{ind[0]}" w:hanging="{ind[1]}"/>'
    if jc: ppr += f'<w:jc w:val="{jc}"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{runs(text, sz, b, i)}</w:p>"

def heading(text, lvl):
    sz = 28 if lvl == 2 else 24
    return (f'<w:p><w:pPr><w:pStyle w:val="Heading{lvl}"/><w:keepNext/><w:spacing w:after="0" w:before="200" w:line="360" w:lineRule="auto"/></w:pPr>'
            f'<w:r><w:rPr>{RF}<w:b/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def code(lines):
    return "".join(f'<w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/><w:sz w:val="15"/><w:szCs w:val="15"/></w:rPr><w:t xml:space="preserve">{esc(l)}</w:t></w:r></w:p>' for l in lines) + para("", after=60)

def table(rows):
    hdr, body = rows[0], rows[1:]
    n = len(hdr); tot = 9360
    first = 1500 if n >= 5 else (1800 if n >= 3 else 3000)
    if n == 1: widths = [tot]
    else:
        # give wider first (+second for fix table) columns, split rest evenly
        rest = (tot - first) // (n - 1); widths = [first] + [rest] * (n - 1); widths[-1] += tot - sum(widths)
    brd = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="808080"/>' for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    def cell(t, w, head=False):
        shd = '<w:shd w:val="clear" w:color="auto" w:fill="E8E8E8"/>' if head else ""
        return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}<w:tcMar><w:left w:w="50" w:type="dxa"/><w:right w:w="50" w:type="dxa"/></w:tcMar></w:tcPr>' + \
               f'<w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>{runs(t, 14, head)}</w:p></w:tc>'
    xml = f'<w:tbl><w:tblPr><w:tblW w:w="{tot}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{brd}</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"
    xml += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(cell(t, w, True) for t, w in zip(hdr, widths)) + "</w:tr>"
    for r in body: xml += '<w:tr><w:trPr><w:cantSplit/></w:trPr>' + "".join(cell(t, w) for t, w in zip(r + [""] * (n - len(r)), widths)) + "</w:tr>"
    return xml + "</w:tbl>" + para("", after=80)

imgs = []
def image(path, alt):
    with open(path, "rb") as f: d = f.read()
    wpx, hpx = struct.unpack(">II", d[16:24])
    inch = min(6.3, wpx / 150 * 0.95); cx = int(inch * 914400); cy = int(cx * hpx / wpx)
    k = len(imgs) + 1; name = f"img{k}.png"; imgs.append((name, d)); rid = f"rIdImg{k}"
    drawing = (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
               f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{1000+k}" name="{name}" descr="{esc(alt)}"/>'
               f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
               f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{1000+k}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
               f'<pic:blipFill><a:blip r:embed="{rid}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
               f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
    return f'<w:p><w:pPr><w:keepNext/><w:spacing w:after="60"/><w:jc w:val="center"/></w:pPr>{drawing}</w:p>'

# ---- parse report.md body (after abstract) ----
title = re.search(r"^# (.+)$", md, re.M).group(1).replace("[^1]", "").strip()
abstract = re.search(r"## Abstract\n(.+?)\n\n## ", md, re.S).group(1).strip()
rest = md[md.index("\n## 1. Introduction"):]
lines = rest.split("\n"); body = []; i = 0
while i < len(lines):
    L = lines[i]
    if not L.strip() or L.startswith("[^1]:"): i += 1; continue
    if L.startswith("```"):
        j = i + 1; blk = []
        while not lines[j].startswith("```"): blk.append(lines[j]); j += 1
        body.append(code(blk)); i = j + 1; continue
    if L.startswith("## "): body.append(heading(L[3:].strip(), 2)); i += 1; continue
    if L.startswith("### "): body.append(heading(L[4:].strip(), 3)); i += 1; continue
    if L.startswith("!["):
        m = re.match(r"!\[(.*?)\]\((.*?)\)", L); body.append(image(m.group(2), m.group(1))); i += 1; continue
    if L.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            if not re.match(r"^\|[\s\-:|]+\|$", lines[i]): rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
            i += 1
        body.append(table(rows)); continue
    if re.match(r"^\d+\. ", L): body.append(para(re.sub(r"^\d+\. ", "", L), num=5)); i += 1; continue
    if L.startswith("- "): body.append(para(L[2:], num=3, after=60)); i += 1; continue
    # caption / normal / reference
    is_cap = bool(re.match(r"\*\*(Figure|Table) ", L))
    prev = body[-1] if body else ""
    ref = bool(re.match(r"^[A-Z][A-Za-z\-]+, [A-Z]\.", L))
    body.append(para(L, jc="both" if not (is_cap or ref) else None, sz=18 if is_cap else None, ind=(540, 540) if ref else None, after=100 if not is_cap else 160)); i += 1

# ---- edit template ----
x = x.replace("PROJECT TITLE", esc(title))
# authors: rebuild the 3x2 author table as 1 row x 2 cols
a = x.index("Author name 1"); t0 = x.rfind("<w:tbl>", 0, a); t1 = x.index("</w:tbl>", a) + len("</w:tbl>")
cellx = lambda n: (f'<w:tc><w:tcPr><w:tcW w:w="3600" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:spacing w:after="120"/><w:jc w:val="center"/></w:pPr>'
                   f'<w:r><w:rPr>{RF}<w:b/></w:rPr><w:t xml:space="preserve">{n}</w:t></w:r><w:r><w:rPr>{RF}</w:rPr><w:br/><w:t xml:space="preserve">[affiliation]</w:t></w:r></w:p></w:tc>')
auth = ('<w:tbl><w:tblPr><w:tblW w:w="7200" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid><w:gridCol w:w="3600"/><w:gridCol w:w="3600"/></w:tblGrid><w:tr>'
        + cellx("Hồ Lê Minh Thạch") + cellx("Bùi Minh Nhật") + "</w:tr></w:tbl>")
x = x[:t0] + auth + x[t1:]
# abstract paragraph(s) inside its table cell
k = x.index("Summarize your project"); p0 = x.rfind("<w:p ", 0, k); p1 = x.index("</w:p>", k) + 6
x = x[:p0] + f'<w:p><w:pPr><w:spacing w:after="200" w:line="240" w:lineRule="auto"/><w:ind w:left="540" w:right="45"/><w:jc w:val="both"/></w:pPr>{runs(abstract)}</w:p>' + x[p1:]
# remove the instruction box table (contains "How to use this template")
h = x.index("How to use this template"); tb0 = x.rfind("<w:tbl>", 0, h); tb1 = x.index("</w:tbl>", h) + 8
x = x[:tb0] + x[tb1:]
# replace everything from the "1. Introduction" heading up to the final sectPr
h1 = x.index("1. Introduction"); p0 = x.rfind("<w:p ", 0, h1); s0 = x.rindex("<w:sectPr")
x = x[:p0] + "".join(body) + x[s0:]
open(f"{W}/word/document.xml", "w", encoding="utf8").write(x)
# media, rels, content types
os.makedirs(f"{W}/word/media", exist_ok=True)
rels = open(f"{W}/word/_rels/document.xml.rels", encoding="utf8").read()
rels = rels.replace("</Relationships>", "".join(f'<Relationship Id="rIdImg{k+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{n}"/>' for k, (n, d) in enumerate(imgs)) + "</Relationships>")
open(f"{W}/word/_rels/document.xml.rels", "w", encoding="utf8").write(rels)
for n, d in imgs: open(f"{W}/word/media/{n}", "wb").write(d)
ct = open(f"{W}/[Content_Types].xml", encoding="utf8").read()
if 'Extension="png"' not in ct: ct = ct.replace("<Override", '<Default Extension="png" ContentType="image/png"/><Override', 1)
open(f"{W}/[Content_Types].xml", "w", encoding="utf8").write(ct)
if os.path.exists(out): os.remove(out)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    names = ["[Content_Types].xml"] + [os.path.relpath(os.path.join(r, f), W) for r, _, fs in os.walk(W) for f in fs if f != "[Content_Types].xml"]
    for n in names: z.write(os.path.join(W, n), n)
shutil.rmtree(W); print("wrote", out, len(imgs), "images")
