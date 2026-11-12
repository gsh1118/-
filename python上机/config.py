import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")
VECTOR_DIR = os.path.join(BASE_DIR, "data", "vectors")

API_KEY = os.getenv("LLM_API_KEY", "")
API_BASE = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
TOP_K = 5