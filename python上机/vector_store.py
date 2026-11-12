# vector_store.py
import chromadb
from config import VECTOR_DIR

client = chromadb.PersistentClient(path=VECTOR_DIR)

def get_collection(file_hash):
    """每个文件一个集合，名字用指纹"""
    return client.get_or_create_collection(name=f"doc_{file_hash}")

def add_chunks(file_hash, chunks, vectors):
    col = get_collection(file_hash)
    col.add(
        ids=[f"{file_hash}_{c['chunk_id']}" for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=vectors,
        metadatas=[{"page": c["page"]} for c in chunks]
    )

def search(file_hash, query_vector, top_k=5):
    col = get_collection(file_hash)
    res = col.query(query_embeddings=[query_vector], n_results=top_k)
    return res