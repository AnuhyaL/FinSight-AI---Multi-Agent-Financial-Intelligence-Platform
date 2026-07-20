from functools import lru_cache
from sentence_transformers import SentenceTransformer
from backend.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def embed(texts: list[str]) -> list[list[float]]:
    return get_embedding_model().encode(texts, normalize_embeddings=True).tolist()
