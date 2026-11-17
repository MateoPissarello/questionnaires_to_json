import io
import openpyxl

from app.domain.exceptions import CorruptedDocumentError, EmptyDocumentError
from app.domain.ports import DocumentParserPort


class XlsxParser(DocumentParserPort):
    """
    XlsxParser is a concrete implementation of the DocumentParserPort protocol.
    It provides functionality to parse XLSX documents and extract their text content.
    """

    def parse(self, file_bytes: bytes, filename: str = "") -> str:
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            sheets_content: list[str] = []

            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                sheet_rows: list[str] = []

                for row in sheet.iter_rows(values_only=True):
                    cell_values = [
                        str(cell).strip()
                        for cell in row
                        if cell is not None and str(cell).strip()
                    ]
                    if cell_values:
                        sheet_rows.append(" | ".join(cell_values))

                if sheet_rows:
                    sheets_content.append(
                        f"--- Sheet: {sheet_name} ---\n" + "\n".join(sheet_rows)
                    )
        except Exception as e:
            raise CorruptedDocumentError(
                f"Could not read XLSX '{filename}': {e}"
            ) from e

        full_text = "\n\n".join(sheets_content).strip()
        if not full_text:
            raise EmptyDocumentError(
                f"The XLSX '{filename}' contains no extractable text."
            )

        return full_text
