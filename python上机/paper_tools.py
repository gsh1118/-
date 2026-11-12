import jieba
from rank_bm25 import BM25Okapi

from config import MODEL_NAME
from qa import get_client, build_context, SYSTEM_PROMPT


def _retrieve(chunks, query, top_k=5):
    """BM25 关键词检索，返回相关段落（无需向量库，可用于单文档/多文档）"""
    if not chunks:
        return []
    corpus = [list(jieba.cut(c["text"])) for c in chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(list(jieba.cut(query)))
    idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [chunks[i] for i in idx]


def _llm(user_prompt):
    client = get_client()
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content


def summarize_structure(chunks):
    """一键梳理研究脉络：研究问题/痛点/方法/实验/结论/局限"""
    dims = {
        "研究问题": "研究问题 本文 研究目标 研究对象",
        "痛点": "不足 挑战 缺陷 问题 局限性",
        "方法": "方法 提出 框架 模型 算法 设计",
        "实验": "实验 数据集 结果 对比 评估 性能",
        "结论": "结论 总结 表明 证明",
        "局限": "局限 不足 未来工作 展望",
    }
    sections = {}
    for name, query in dims.items():
        top = _retrieve(chunks, query, top_k=5)
        if not top:
            sections[name] = "未检索到明确依据"
            continue
        ctx = build_context(top)
        sections[name] = _llm(
            f"请基于下面的原文片段，用2-3句话归纳这篇文档的「{name}」。"
            f"每个结论后面用 [n] 标注引用的片段编号；若原文找不到依据，直接说“文档中未找到明确依据”。\n\n原文片段：\n{ctx}"
        )
    return sections


def compare_papers(paper_chunks_list, dimensions):
    """多篇论文对比，每个格子必须带引用来源"""
    table = []
    for dim in dimensions:
        row = {"维度": dim}
        for i, chunks in enumerate(paper_chunks_list, start=1):
            top = _retrieve(chunks, dim, top_k=4)
            if not top:
                row[f"论文{i}"] = "未检索到明确依据"
            else:
                ctx = build_context(top)
                row[f"论文{i}"] = _llm(
                    f"请只用下面的原文片段，说明这篇论文在「{dim}」方面的具体情况（2-3句话），"
                    f"必须用 [n] 标注引用来源；找不到依据就说“文档中未找到明确依据”。\n\n原文片段：\n{ctx}"
                )
        table.append(row)
    return table


def generate_quiz(chunks, num=3, qtype="choice"):
    """根据文档生成自测题，每题带答案和出处"""
    key = _retrieve(chunks, "核心 方法 结论 结果 定义 关键", top_k=8)
    if not key:
        return "文档中没有足够内容生成题目。"
    ctx = build_context(key)
    if qtype == "choice":
        style = f"生成 {num} 道单选题，每题含 4 个选项、正确答案和一句解析。"
    else:
        style = f"生成 {num} 道简答题，每题含参考答案要点。"
    return _llm(
        f"请基于下面的原文片段，{style}"
        f"每题末尾标注引用的片段编号 [n] 和页码；找不到依据的不要出。\n\n原文片段：\n{ctx}"
    )
