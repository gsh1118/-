from config import CHUNK_SIZE, CHUNK_OVERLAP

def split_pages(pages):
    """把每页文字切成小段，保留页码"""
    chunks = []
    for p in pages:
        text = p["text"]
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            piece = text[start:end]
            if piece.strip():
                chunks.append({
                    "text": piece.strip(),
                    "page": p["page"],
                    "chunk_id": len(chunks)
                })
            start = end - CHUNK_OVERLAP  # 留一点重叠，防止切断句子
    return chunks