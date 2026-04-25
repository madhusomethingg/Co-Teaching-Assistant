"""
vector_store.py — Lightweight vector store using numpy + sentence-transformers.
Replaces ChromaDB entirely. No protobuf, no gRPC, no version conflicts.
"""
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

STORE_PATH = "vector_store"
MODEL_NAME = "all-MiniLM-L6-v2"

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


class VectorStore:
    """Simple cosine-similarity vector store backed by numpy arrays."""

    def __init__(self, name: str):
        self.name = name
        self.docs: list[str] = []
        self.metas: list[dict] = []
        self.embeddings: np.ndarray | None = None

    def add(self, documents: list[str], metadatas: list[dict]):
        model = _get_model()
        embs = model.encode(documents, show_progress_bar=True, batch_size=32)
        self.docs.extend(documents)
        self.metas.extend(metadatas)
        if self.embeddings is None:
            self.embeddings = embs
        else:
            self.embeddings = np.vstack([self.embeddings, embs])

    def query(self, query_text: str, k: int = 4) -> list[dict]:
        if self.embeddings is None or len(self.docs) == 0:
            return []
        model = _get_model()
        q_emb = model.encode([query_text])
        # Cosine similarity
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        normed = self.embeddings / np.clip(norms, 1e-10, None)
        q_norm = q_emb / np.clip(np.linalg.norm(q_emb), 1e-10, None)
        scores = (normed @ q_norm.T).flatten()
        top_k = np.argsort(scores)[::-1][:k]
        return [
            {
                "text": self.docs[i],
                "meta": self.metas[i],
                "score": float(scores[i]),
            }
            for i in top_k
        ]

    def save(self):
        os.makedirs(STORE_PATH, exist_ok=True)
        path = os.path.join(STORE_PATH, f"{self.name}.pkl")
        with open(path, "wb") as f:
            pickle.dump({"docs": self.docs, "metas": self.metas, "embeddings": self.embeddings}, f)
        print(f"  Saved {len(self.docs)} vectors → {path}")

    @classmethod
    def load(cls, name: str) -> "VectorStore":
        path = os.path.join(STORE_PATH, f"{name}.pkl")
        with open(path, "rb") as f:
            data = pickle.load(f)
        store = cls(name)
        store.docs = data["docs"]
        store.metas = data["metas"]
        store.embeddings = data["embeddings"]
        return store

    @classmethod
    def exists(cls, name: str) -> bool:
        return os.path.exists(os.path.join(STORE_PATH, f"{name}.pkl"))
