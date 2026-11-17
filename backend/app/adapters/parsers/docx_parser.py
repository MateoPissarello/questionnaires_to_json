import io
import docx

from app.domain.exceptions import CorruptedDocumentError, EmptyDocumentError
from app.domain.ports import DocumentParserPort


class DocxParser(DocumentParserPort):
    """
    DocxParser is a concrete implementation of the DocumentParserPort protocol.
    It provides functionality to parse DOCX documents and extract their text content.
    """

    def parse(self, file_bytes: bytes, filename: str = "") -> str:
        try:
            reader = docx.Document(io.BytesIO(file_bytes))
            pages_content: list[str] = []
            tables_content: list[str] = []
            for paragraph in reader.paragraphs:
                if paragraph.text.strip():
                    pages_content.append(paragraph.text.strip())
            for table in reader.tables:
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    if any(row_cells):
                        tables_content.append(" | ".join(row_cells))
        except Exception as e:
            raise CorruptedDocumentError(
                f"Could not read DOCX '{filename}': {e}"
            ) from e

        full_text = "\n\n".join(pages_content + tables_content).strip()
        if not full_text:
            raise EmptyDocumentError(
                f"The DOCX '{filename}' contains no extractable text."
            )

        return full_text
