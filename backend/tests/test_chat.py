import pytest
from backend.rag.retriever import retrieve


def test_missing_report_raises() -> None:
    with pytest.raises(LookupError):
        retrieve("not-indexed", "What is revenue?")
