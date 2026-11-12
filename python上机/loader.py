import hashlib, os
from config import UPLOAD_DIR

def save_upload(uploaded_file):
    """把上传的文件存到本地，返回文件路径和指纹"""
    content = uploaded_file.getvalue()
    file_hash = hashlib.md5(content).hexdigest()[:12]
    filename = f"{file_hash}_{uploaded_file.name}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)
    return path, file_hash

def guess_doc_type(text):
    """粗判：是讲义还是论文"""
    paper_signals = ["摘要", "关键词", "参考文献", "Abstract", "References", "实验", "引言"]
    hits = sum(1 for s in paper_signals if s in text[:3000])
    return "paper" if hits >= 3 else "handout"