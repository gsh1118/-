import jieba
from rank_bm25 import BM25Okapi
from embedder import embed_texts
from vector_store import search

def build_bm25(chunks):
    """给一个文件的所有段落建关键词索引"""
    tokenized = [list(jieba.cut(c["text"])) for c in chunks]
    return BM25Okapi(tokenized)

def classify_query(query):
    """判断用户问的是'找原文'还是'要总结'"""
    exact_words = ["第几页", "原文", "在哪", "定义", "出处", "哪一章"]
    if any(w in query for w in exact_words):
        return "exact"
    return "summary"

def retrieve(file_hash, chunks, bm25, query, mode="summary"):
    """两种模式检索"""
    if mode == "exact":
        # 关键词检索为主
        tokens = list(jieba.cut(query))
        scores = bm25.get_scores(tokens)
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
        return [chunks[i] for i in top_idx]
    else:
        # 向量检索为主
        q_vec = embed_texts([query])[0]
        res = search(file_hash, q_vec, top_k=5)
        results = []
        for i, doc in enumerate(res["documents"][0]):
            results.append({
                "text": doc,
                "page": res["metadatas"][0][i]["page"]
            })
        return results