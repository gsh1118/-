import json, os
from config import CACHE_DIR

def cache_path(file_hash):
    return os.path.join(CACHE_DIR, f"{file_hash}.json")

def load_cache(file_hash):
    p = cache_path(file_hash)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_cache(file_hash, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path(file_hash), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)