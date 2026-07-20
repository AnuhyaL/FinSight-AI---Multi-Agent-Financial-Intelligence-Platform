from langchain_text_splitters import RecursiveCharacterTextSplitter
from .pdf_parser import PageText


def chunk_pages(pages: list[PageText]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks: list[dict] = []
    for page in pages:
        for index, text in enumerate(splitter.split_text(page.text)):
            chunks.append({"text": text, "page": page.page, "chunk": index})
    return chunks
