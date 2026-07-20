import fitz
from backend.rag.pdf_parser import extract_pdf_pages


def test_extract_pdf_pages(tmp_path) -> None:
    path = tmp_path / "report.pdf"
    document = fitz.open(); page = document.new_page(); page.insert_text((72, 72), "Revenue was strong."); document.save(path); document.close()
    pages = extract_pdf_pages(path)
    assert pages[0].page == 1
    assert "Revenue" in pages[0].text
