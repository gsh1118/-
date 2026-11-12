from openai import OpenAI
from config import API_KEY, API_BASE, MODEL_NAME

_client = None

def get_client():
    """延迟创建客户端，避免没配 Key 时 import 直接报错"""
    global _client
    if not API_KEY:
        raise RuntimeError("未配置 LLM_API_KEY，请先设置环境变量后再提问")
    if _client is None:
        _client = OpenAI(api_key=API_KEY, base_url=API_BASE)
    return _client

SYSTEM_PROMPT = """你是一个严格的文档问答助手。规则：
1. 只根据下面提供的原文片段回答，不许编造。
2. 每个结论后面用 [1][2] 标注引用了第几段。
3. 如果原文里找不到依据，直接说"文档中未找到明确依据"，不要猜。
"""

def build_context(chunks):
    """把检索到的段落拼成带编号的上下文"""
    lines = []
    for i, c in enumerate(chunks, start=1):
        lines.append(f"[{i}] (第{c['page']}页) {c['text']}")
    return "\n\n".join(lines)

def answer(query, chunks):
    context = build_context(chunks)
    resp = get_client().chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"原文片段：\n{context}\n\n问题：{query}"}
        ],
        temperature=0.2
    )
    return resp.choices[0].message.content

def verify_citation(answer_text, chunks):
    """简单校验：答案里的数字/关键词是否出现在引用片段里"""
    # 简化版：检查答案里有没有 [n] 标注
    import re
    cited = re.findall(r"\[(\d+)\]", answer_text)
    return len(cited) > 0