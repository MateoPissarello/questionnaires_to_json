from pathlib import Path
from typing import Optional
from app.adapters.parsers.docx_parser import DocxParser
from app.adapters.parsers.pdf_parser import PdfParser
from app.adapters.parsers.xlsx_parser import XlsxParser
from app.domain.ports import DocumentParserPort
from app.domain.exceptions import (
    UnsupportedFileFormatError,
    FileTooLargeError,
    EmptyDocumentError,
)


class ParserService:
    def __init__(
        self,
        parsers: Optional[dict[str, DocumentParserPort]] = None,
        max_file_size_bytes: int = 20 * 1024 * 1024,  # Default to 20 MB
    ):
        self._parsers: dict[str, DocumentParserPort] = parsers or {
            ".pdf": PdfParser(),
            ".docx": DocxParser(),
            ".xlsx": XlsxParser(),
        }
        self._max_file_size_bytes = max_file_size_bytes

    def validate_file(self, file_bytes: bytes, filename: str) -> str:
        file_extension = Path(filename).suffix.lower()
        if file_extension not in self._parsers:
            raise UnsupportedFileFormatError(
                f"Unsupported file format: '{file_extension}'. Supported formats are: {list(self._parsers.keys())}"
            )
        if len(file_bytes) == 0:
            raise EmptyDocumentError(f"The file '{filename}' is empty.")
        if len(file_bytes) > self._max_file_size_bytes:
            raise FileTooLargeError(
                f"File size exceeds the maximum allowed limit of {self._max_file_size_bytes / (1024 * 1024)} MB."
            )
        return file_extension

    def parse_document(self, file_bytes: bytes, filename: str) -> str:
        ext = self.validate_file(file_bytes, filename)
        parser = self._parsers[ext]
        return parser.parse(file_bytes, filename)
