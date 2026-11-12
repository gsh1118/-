from docx import Document

def export_qa(records, path):
    """导出问答记录到 Word"""
    doc = Document()
    doc.add_heading("问答记录", level=1)
    for i, r in enumerate(records, start=1):
        doc.add_heading(f"问题 {i}：{r['question']}", level=2)
        doc.add_paragraph(f"回答：{r['answer']}")
        doc.add_paragraph(f"出处：第 {r['page']} 页")
        doc.add_paragraph(f"原文：{r['source_text'][:200]}...")
    doc.save(path)

def export_outline(chunks, path):
    """导出简易复习提纲"""
    doc = Document()
    doc.add_heading("复习提纲", level=1)
    for c in chunks[:30]:  # 先简单取前 30 段
        doc.add_paragraph(f"第{c['page']}页：{c['text'][:80]}...")
    doc.save(path)