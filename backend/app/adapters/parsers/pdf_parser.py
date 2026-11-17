import io
from pypdf import PdfReader

from app.domain.exceptions import CorruptedDocumentError, EmptyDocumentError
from app.domain.ports import DocumentParserPort


class PdfParser(DocumentParserPort):
    """
    PdfParser is a concrete implementation of the DocumentParserPort protocol.
    It provides functionality to parse PDF documents and extract their text content.
    """

    def parse(self, file_bytes: bytes, filename: str = "") -> str:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            pages_content: list[str] = []
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = (page.extract_text() or "").strip()
                if page_text:
                    pages_content.append(f"--- Page {page_num} ---\n{page_text}")
        except Exception as e:
            raise CorruptedDocumentError(f"Could not read PDF '{filename}': {e}") from e

        full_text = "\n\n".join(pages_content).strip()
        if not full_text:
            raise EmptyDocumentError(
                f"The PDF '{filename}' contains no extractable text."
            )

        return full_text


PDFParser = PdfParser
