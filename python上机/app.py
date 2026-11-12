import os
import html
import re
import tempfile

import streamlit as st
import pandas as pd

from loader import save_upload, guess_doc_type
from parser import parse_pdf, parse_txt, extract_figures_tables
from splitter import split_pages
from embedder import embed_texts
from vector_store import add_chunks
from retriever import build_bm25, classify_query, retrieve
from qa import answer
from cache import load_cache, save_cache
from paper_tools import summarize_structure, compare_papers, generate_quiz
from exporter import export_qa, export_outline

st.set_page_config(page_title="文献与讲义精读助手", layout="wide")
st.title("📚 文献与讲义智能精读助手")

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def parse_file(path):
    if path.lower().endswith(".txt"):
        return parse_txt(path)
    return parse_pdf(path)


def _highlight(text, query):
    """把原文片段中命中的查询词用 <mark> 高亮"""
    terms = [t for t in query.split() if t]
    if query.strip():
        terms.append(query.strip())
    terms = sorted({t for t in terms if t}, key=len, reverse=True)
    safe = html.escape(text)
    if not terms:
        return safe
    pattern = re.compile("|".join(re.escape(html.escape(t)) for t in terms))
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", safe)


def _export_bytes(builder, tag):
    p = os.path.join(tempfile.gettempdir(), f"jj_export_{tag}.docx")
    builder(p)
    with open(p, "rb") as f:
        return f.read()


def _load_or_parse(path, file_hash):
    cached = load_cache(file_hash)
    if cached:
        return cached["chunks"], cached.get("doc_type"), cached.get("figures", [])
    pages = parse_file(path)
    chunks = split_pages(pages)
    doc_type = guess_doc_type("".join(p["text"] for p in pages))
    figures = extract_figures_tables(pages)
    vectors = embed_texts([c["text"] for c in chunks])
    add_chunks(file_hash, chunks, vectors)
    save_cache(file_hash, {"chunks": chunks, "doc_type": doc_type, "figures": figures})
    return chunks, doc_type, figures


def _handout_mode():
    uploaded = st.file_uploader("上传 PDF 或 TXT", type=["pdf", "txt"], key="handout_upload")
    if not uploaded:
        return

    path, file_hash = save_upload(uploaded)
    with st.spinner("正在解析文档..."):
        chunks, doc_type, figures = _load_or_parse(path, file_hash)
    st.success("解析完成")
    st.info(f"自动识别：这更像一篇{'论文' if doc_type == 'paper' else '讲义'}")

    query = st.text_input("输入你的问题")
    if query and st.button("提问"):
        q_mode = classify_query(query)
        bm25 = build_bm25(chunks)
        results = retrieve(file_hash, chunks, bm25, query, q_mode)
        with st.spinner("正在回答..."):
            ans = answer(query, results)
        st.markdown("### 回答")
        st.write(ans)
        st.markdown("### 出处（高亮为命中关键词）")
        for i, r in enumerate(results, start=1):
            st.markdown(f"**[{i}] 第 {r['page']} 页**")
            st.markdown(_highlight(r["text"][:300], query), unsafe_allow_html=True)
        st.session_state.qa_records.append({
            "question": query,
            "answer": ans,
            "page": results[0]["page"] if results else None,
            "source_text": results[0]["text"] if results else "",
        })

    st.markdown("---")
    if st.session_state.qa_records:
        st.download_button(
            "⬇️ 下载问答记录（Word）",
            data=_export_bytes(lambda p: export_qa(st.session_state.qa_records, p), "qa"),
            file_name="问答记录.docx",
            mime=DOCX_MIME,
        )
    st.download_button(
        "⬇️ 下载复习提纲（Word）",
        data=_export_bytes(lambda p: export_outline(chunks, p), "outline"),
        file_name="复习提纲.docx",
        mime=DOCX_MIME,
    )


def _paper_mode():
    files = st.file_uploader(
        "上传一篇或多篇论文（PDF 或 TXT）", type=["pdf", "txt"],
        accept_multiple_files=True, key="paper_upload"
    )
    if not files:
        st.info("请先上传论文")
        return

    papers = []
    for f in files:
        path, file_hash = save_upload(f)
        with st.spinner(f"正在解析 {f.name}..."):
            chunks, doc_type, figures = _load_or_parse(path, file_hash)
        papers.append({"name": f.name, "chunks": chunks, "figures": figures, "doc_type": doc_type})

    for i, p in enumerate(papers, start=1):
        st.caption(f"论文{i}：{p['name']} → {'论文' if p['doc_type'] == 'paper' else '讲义'}")

    tab1, tab2, tab3, tab4 = st.tabs(["单文档深度梳理", "跨文献对比", "自测题生成", "图表公式"])

    with tab1:
        if len(papers) > 1:
            names = [p["name"] for p in papers]
            pick = st.selectbox("选择要梳理的文档", names)
            chunks = papers[names.index(pick)]["chunks"]
        else:
            chunks = papers[0]["chunks"]
        if st.button("一键生成研究脉络梳理"):
            with st.spinner("正在梳理..."):
                try:
                    sections = summarize_structure(chunks)
                except Exception as e:
                    st.error(str(e))
                    sections = None
            if sections:
                for name, text in sections.items():
                    st.markdown(f"### {name}")
                    st.write(text)

    with tab2:
        if len(papers) < 2:
            st.info("跨文献对比至少需要两篇论文，请在上方多上传几篇")
        else:
            dims_input = st.text_input("对比维度（逗号分隔）", value="研究问题,方法,实验,结论")
            dims = [d.strip() for d in dims_input.split(",") if d.strip()]
            if st.button("开始对比"):
                with st.spinner("正在对比..."):
                    try:
                        table = compare_papers([p["chunks"] for p in papers], dims)
                    except Exception as e:
                        st.error(str(e))
                        table = None
                if table:
                    st.dataframe(pd.DataFrame(table), use_container_width=True)

    with tab3:
        num = st.slider("题目数量", 1, 10, 3)
        qtype = st.radio("题型", ["choice", "short"],
                         format_func=lambda x: "选择题" if x == "choice" else "简答题",
                         horizontal=True)
        if st.button("生成自测题"):
            with st.spinner("正在出题..."):
                try:
                    quiz = generate_quiz(papers[0]["chunks"], num=num, qtype=qtype)
                except Exception as e:
                    st.error(str(e))
                    quiz = None
            if quiz:
                st.markdown(quiz)

    with tab4:
        for i, p in enumerate(papers, start=1):
            st.markdown(f"**论文{i}：{p['name']}**")
            if p["figures"]:
                for it in p["figures"]:
                    st.markdown(f"- `{it['type']}`（第 {it['page']} 页）：{it['content']}")
            else:
                st.caption("未识别到图表/公式标题")


if "qa_records" not in st.session_state:
    st.session_state.qa_records = []

mode = st.radio("选择模式", ["讲义模式", "论文精读模式"], horizontal=True)

if mode == "讲义模式":
    _handout_mode()
else:
    _paper_mode()
