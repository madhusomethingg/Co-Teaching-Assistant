"""
vector_store.py — BM25-based retrieval store.
Pure Python. No PyTorch, no sentence-transformers, no C extensions.
Works on any Python version including 3.14.
"""
import os
import re
import pickle
from rank_bm25 import BM25Okapi

STORE_PATH = "vector_store"


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


class VectorStore:
    def __init__(self, name: str):
        self.name = name
        self.docs: list[str] = []
        self.metas: list[dict] = []
        self._bm25: BM25Okapi | None = None

    def add(self, documents: list[str], metadatas: list[dict]):
        self.docs.extend(documents)
        self.metas.extend(metadatas)
        tokenized = [_tokenize(d) for d in self.docs]
        self._bm25 = BM25Okapi(tokenized)
        print(f"  Built BM25 index over {len(self.docs)} docs")

    def query(self, query_text: str, k: int = 4) -> list[dict]:
        if self._bm25 is None or not self.docs:
            return []
        tokens = _tokenize(query_text)
        scores = self._bm25.get_scores(tokens)
        top_k = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        max_score = max(scores[i] for i in top_k) or 1.0
        return [
            {
                "text": self.docs[i],
                "meta": self.metas[i],
                "score": float(scores[i] / max_score),  # normalised 0-1
            }
            for i in top_k
        ]

    def save(self):
        os.makedirs(STORE_PATH, exist_ok=True)
        path = os.path.join(STORE_PATH, f"{self.name}.pkl")
        with open(path, "wb") as f:
            pickle.dump({"docs": self.docs, "metas": self.metas, "bm25": self._bm25}, f)
        print(f"  Saved → {path}")

    @classmethod
    def load(cls, name: str) -> "VectorStore":
        path = os.path.join(STORE_PATH, f"{name}.pkl")
        with open(path, "rb") as f:
            data = pickle.load(f)
        store = cls(name)
        store.docs = data["docs"]
        store.metas = data["metas"]
        store._bm25 = data["bm25"]
        return store

    @classmethod
    def exists(cls, name: str) -> bool:
        return os.path.exists(os.path.join(STORE_PATH, f"{name}.pkl"))
