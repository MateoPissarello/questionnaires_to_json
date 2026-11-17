import io
import docx
import openpyxl
import pytest
from pypdf import PdfWriter

from app.domain.exceptions import (
    CorruptedDocumentError,
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileFormatError,
)
from app.services.parser_service import ParserService


def _create_docx_bytes(
    paragraphs: list[str] | None = None,
    table_rows: list[list[str]] | None = None,
) -> bytes:
    """Helper para generar un archivo .docx válido en memoria."""
    doc = docx.Document()
    for text in paragraphs or []:
        doc.add_paragraph(text)
    if table_rows:
        cols = len(table_rows[0])
        table = doc.add_table(rows=0, cols=cols)
        for row_data in table_rows:
            row_cells = table.add_row().cells
            for idx, value in enumerate(row_data):
                row_cells[idx].text = value
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _create_xlsx_bytes(rows: list[list[object]] | None = None) -> bytes:
    """Helper para generar un archivo .xlsx válido en memoria."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Cuestionario"
    for row in rows or []:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _create_blank_pdf_bytes() -> bytes:
    """Helper para generar un PDF válido pero con página en blanco (sin texto)."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _create_text_pdf_bytes(text: str = "Questionario di esempio") -> bytes:
    """Helper para generar un PDF minimalista válido con texto extraíble en memoria."""
    from pypdf.generic import (
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
    )

    writer = PdfWriter()
    page = writer.add_blank_page(width=400, height=400)

    font_dict = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    resources = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_dict})}
    )
    page[NameObject("/Resources")] = resources

    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 50 350 Td ({text}) Tj ET".encode("latin1"))
    page[NameObject("/Contents")] = writer._add_object(stream)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.mark.parametrize(
    "invalid_filename",
    ["cuestionario.txt", "datos.csv", "antiguo.doc", "imagen.png", "sin_extension"],
)
def test_validate_file_rejects_unsupported_extensions(invalid_filename: str) -> None:
    """Verifica que extensiones no soportadas lancen UnsupportedFileFormatError."""
    service = ParserService()
    with pytest.raises(UnsupportedFileFormatError):
        service.validate_file(b"contenido de prueba", invalid_filename)


def test_validate_file_rejects_empty_and_oversized_files() -> None:
    """Verifica que archivos de 0 bytes o que superen el límite lancen excepción."""
    service = ParserService(max_file_size_bytes=100)

    with pytest.raises(EmptyDocumentError):
        service.validate_file(b"", "test.pdf")

    with pytest.raises(FileTooLargeError):
        service.validate_file(b"x" * 101, "test.pdf")


@pytest.mark.parametrize("filename", ["corrupto.pdf", "corrupto.docx", "corrupto.xlsx"])
def test_parsers_raise_corrupted_document_error_on_invalid_bytes(filename: str) -> None:
    """Verifica que bytes basura en cualquiera de los 3 formatos lancen CorruptedDocumentError."""
    service = ParserService()
    with pytest.raises(CorruptedDocumentError):
        service.parse_document(b"estos no son bytes validos de archivo", filename)


def test_docx_parser_extracts_paragraphs_and_tables() -> None:
    """Verifica extracción de párrafos y tablas (ej. escalas Likert) en .docx."""
    service = ParserService()
    docx_bytes = _create_docx_bytes(
        paragraphs=["Cuestionario de Ansiedad", "1. Me preocupo fácilmente."],
        table_rows=[
            ["Ítem", "Nunca (0)", "A veces (1)", "Siempre (2)"],
            ["2. Me cuesta relajarme.", "0", "1", "2"],
        ],
    )

    extracted = service.parse_document(docx_bytes, "EVALUACION.DOCX")

    assert "Cuestionario de Ansiedad" in extracted
    assert "1. Me preocupo fácilmente." in extracted
    assert "2. Me cuesta relajarme. | 0 | 1 | 2" in extracted


def test_docx_parser_raises_empty_document_error_when_blank() -> None:
    """Verifica que un .docx válido pero sin texto lance EmptyDocumentError."""
    service = ParserService()
    empty_docx = _create_docx_bytes(paragraphs=["   "], table_rows=[["", "  "]])

    with pytest.raises(EmptyDocumentError):
        service.parse_document(empty_docx, "vacio.docx")


def test_xlsx_parser_extracts_sheet_rows_and_ignores_blank_cells() -> None:
    """Verifica extracción de hojas y filas en .xlsx."""
    service = ParserService()
    xlsx_bytes = _create_xlsx_bytes(
        rows=[
            ["Numero", "Enunciado", "Tipo", "Opciones"],
            [1, "¿Cuál es la capital de Italia?", "seleccion_multiple", "A) Roma | B) Milán"],
            [None, "   ", None, None],
        ]
    )

    extracted = service.parse_document(xlsx_bytes, "banco_items.xlsx")

    assert "--- Sheet: Cuestionario ---" in extracted
    assert "1 | ¿Cuál es la capital de Italia? | seleccion_multiple" in extracted


def test_xlsx_parser_raises_empty_document_error_when_blank() -> None:
    """Verifica que un .xlsx sin celdas con texto lance EmptyDocumentError."""
    service = ParserService()
    empty_xlsx = _create_xlsx_bytes(rows=[[None, "   ", None]])

    with pytest.raises(EmptyDocumentError):
        service.parse_document(empty_xlsx, "vacio.xlsx")


def test_pdf_parser_extracts_real_pdf_and_rejects_blank_pdf() -> None:
    """Verifica que PdfParser extraiga texto de un PDF real y rechace un PDF en blanco."""
    service = ParserService()

    # 1. PDF en blanco debe lanzar EmptyDocumentError
    blank_pdf = _create_blank_pdf_bytes()
    with pytest.raises(EmptyDocumentError):
        service.parse_document(blank_pdf, "blanco.pdf")

    # 2. PDF válido con texto generado en memoria
    valid_pdf = _create_text_pdf_bytes("Questionario di esempio - Item 1")
    extracted = service.parse_document(valid_pdf, "enunciado.pdf")
    assert "--- Page 1 ---" in extracted
    assert "Questionario di esempio - Item 1" in extracted


def test_examples_folder_deliverables_are_valid() -> None:
    """Verifica que los 3 documentos (.pdf, .docx, .xlsx) y sus .json en /examples sean válidos."""
    from pathlib import Path
    from app.domain.schemas import QuestionnaireOutput

    examples_dir = Path(__file__).resolve().parents[2] / "examples"
    service = ParserService()

    expected_pairs = [
        ("questionario_esempio_it.pdf", "questionario_esempio_it.json"),
        ("cuestionario_psicometrico_es.docx", "cuestionario_psicometrico_es.json"),
        ("cognitive_assessment_en.xlsx", "cognitive_assessment_en.json"),
    ]

    for doc_name, json_name in expected_pairs:
        doc_path = examples_dir / doc_name
        json_path = examples_dir / json_name
        assert doc_path.exists(), f"Missing {doc_path}"
        assert json_path.exists(), f"Missing {json_path}"

        extracted_text = service.parse_document(doc_path.read_bytes(), doc_name)
        assert len(extracted_text) > 50

        validated_json = QuestionnaireOutput.model_validate_json(
            json_path.read_text(encoding="utf-8")
        )
        assert validated_json.total_items == len(validated_json.items)
