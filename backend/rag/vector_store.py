import re
from pathlib import Path
import chromadb
from chromadb.errors import NotFoundError
from backend.config import settings
from .embeddings import embed


def _safe_collection(report_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "-", report_id)[:60] or "report"


def _client() -> chromadb.PersistentClient:
    Path(settings.chroma_dir).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=settings.chroma_dir)


def index_chunks(report_id: str, chunks: list[dict]) -> int:
    collection = _client().get_or_create_collection(_safe_collection(report_id))
    collection.upsert(ids=[f"{report_id}-{i}" for i in range(len(chunks))],
                      documents=[item["text"] for item in chunks],
                      embeddings=embed([item["text"] for item in chunks]),
                      metadatas=[{"page": item["page"], "chunk": item["chunk"]}
                                 for item in chunks])
    return len(chunks)


def search(report_id: str, query: str, limit: int = 4) -> list[dict]:
    try:
        result = _client().get_collection(_safe_collection(report_id)).query(
            query_embeddings=embed([query]), n_results=limit)
    except (ValueError, NotFoundError) as exc:
        raise LookupError("Report has not been indexed yet.") from exc
    return [{"text": text, **metadata} for text, metadata in zip(
        result["documents"][0], result["metadatas"][0])]
