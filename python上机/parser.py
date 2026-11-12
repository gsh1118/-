import fitz  # PyMuPDF
import re

def parse_pdf(path):
    """返回一段一段的文字，每段带页码"""
    doc = fitz.open(path)
    pages = []
    for page_no, page in enumerate(doc, start=1):
        text = page.get_text("text")
        pages.append({"page": page_no, "text": text})
    doc.close()
    return pages

def parse_txt(path):
    """解析 TXT：按空行分段，每段当作一页"""
    text = None
    for enc in ("utf-8", "gbk", "utf-16"):
        try:
            with open(path, "r", encoding=enc) as f:
                text = f.read()
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("无法识别 TXT 编码")
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    if not blocks:
        blocks = [text.strip()]
    return [{"page": i, "text": b} for i, b in enumerate(blocks, start=1)]

def extract_figures_tables(pages):
    """从文字里用正则找图题、表注、公式编号"""
    items = []
    fig_pattern = re.compile(r"(图\s*\d+[：:.\s].{0,80})")
    tab_pattern = re.compile(r"(表\s*\d+[：:.\s].{0,80})")
    eq_pattern = re.compile(r"(公式\s*\(?\d+\)?.{0,80})")
    for p in pages:
        for pat, kind in [(fig_pattern, "figure"), (tab_pattern, "table"), (eq_pattern, "formula")]:
            for m in pat.findall(p["text"]):
                items.append({"type": kind, "content": m.strip(), "page": p["page"]})
    return items