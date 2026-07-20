from dataclasses import dataclass
from pathlib import Path
import fitz


@dataclass(frozen=True)
class PageText:
    page: int
    text: str


def extract_pdf_pages(path: Path) -> list[PageText]:
    """Extract non-empty page text and return helpful validation errors."""
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path.name}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF annual reports are supported.")
    try:
        with fitz.open(path) as document:
            pages = [PageText(i + 1, page.get_text("text").strip())
                     for i, page in enumerate(document)]
    except fitz.FileDataError as exc:
        raise ValueError("The uploaded file is not a readable PDF.") from exc
    pages = [page for page in pages if page.text]
    if not pages:
        raise ValueError("No extractable text was found in this PDF.")
    return pages
