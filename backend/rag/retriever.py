from backend.models import Source
from .vector_store import search


def retrieve(report_id: str, question: str) -> tuple[str, list[Source]]:
    results = search(report_id, question)
    sources = [Source(page=int(item["page"]), excerpt=item["text"][:300]) for item in results]
    context = "\n\n".join(f"[Page {item['page']}] {item['text']}" for item in results)
    return context, sources
