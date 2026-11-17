import asyncio
import io
import docx
import openpyxl
from httpx import ASGITransport, AsyncClient

from app.adapters.queue.memory_queue import InMemoryJobQueue
from app.api.dependencies import get_job_queue, get_llm_extractor, get_parser_service
from app.domain.exceptions import NoItemsDetectedError
from app.domain.ports import LLMExtractorPort
from app.domain.schemas import (
    AlternativeSchema,
    QuestionItemSchema,
    QuestionnaireOutput,
)
from app.main import app
from app.services.extraction_worker import ExtractionWorker
from app.services.parser_service import ParserService


class _FakeLLMExtractor(LLMExtractorPort):
    """Fake LLM extractor para pruebas de integración HTTP sin llamadas externas."""

    def __init__(self, should_raise: Exception | None = None) -> None:
        self._should_raise = should_raise

    async def extract_questionnaire(
        self, raw_text: str, filename: str
    ) -> QuestionnaireOutput:
        if self._should_raise is not None:
            raise self._should_raise

        return QuestionnaireOutput(
            titulo=f"Cuestionario desde {filename}",
            idioma="it",
            total_items=2,
            items=[
                QuestionItemSchema(
                    numero=1,
                    enunciado="Mi preoccupo eccessivamente per cose di poca importanza.",
                    tipo="escala_likert",
                    alternativas=[
                        AlternativeSchema(valor=0, texto="Mai"),
                        AlternativeSchema(valor=1, texto="A volte"),
                        AlternativeSchema(valor=2, texto="Spesso"),
                        AlternativeSchema(valor=3, texto="Sempre"),
                    ],
                    respuesta_correcta=None,
                ),
                QuestionItemSchema(
                    numero=2,
                    enunciado="Quale numero completa la serie: 2, 4, 8, 16, ...?",
                    tipo="seleccion_multiple",
                    alternativas=[
                        AlternativeSchema(valor="A", texto="18"),
                        AlternativeSchema(valor="B", texto="24"),
                        AlternativeSchema(valor="C", texto="32"),
                    ],
                    respuesta_correcta="C",
                ),
            ],
        )


def _make_docx_bytes(text: str = "1. Pregunta de prueba") -> bytes:
    doc = docx.Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _make_xlsx_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["Numero", "Enunciado", "Tipo"])
    ws.append([1, "Pregunta en Excel", "desarrollo"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


async def test_health_endpoint() -> None:
    """Verifica que GET /health responda 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_extract_endpoint_returns_standardized_json() -> None:
    """Verifica que POST /api/v1/questionnaires/extract retorne 200 y el JSON esperado."""
    app.dependency_overrides[get_llm_extractor] = lambda: _FakeLLMExtractor()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/questionnaires/extract",
                files={
                    "file": (
                        "esempio.docx",
                        _make_docx_bytes("Questionario di esempio"),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["titulo"] == "Cuestionario desde esempio.docx"
        assert data["idioma"] == "it"
        assert data["total_items"] == 2
        assert data["items"][0]["tipo"] == "escala_likert"
        assert data["items"][0]["alternativas"][0]["valor"] == 0
        assert data["items"][1]["respuesta_correcta"] == "C"
    finally:
        app.dependency_overrides.clear()


async def test_extract_endpoint_maps_domain_errors_to_http_codes() -> None:
    """Verifica códigos HTTP semánticos (400 formato inválido, 422 vacío/corrupto/sin ítems)."""
    app.dependency_overrides[get_llm_extractor] = lambda: _FakeLLMExtractor()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Extensión no soportada (.txt) -> 400
            res_bad_ext = await client.post(
                "/api/v1/questionnaires/extract",
                files={"file": ("notas.txt", b"hola mundo", "text/plain")},
            )
            assert res_bad_ext.status_code == 400
            assert res_bad_ext.json()["code"] == "UNSUPPORTED_FILE_FORMAT"

            # 2. Archivo vacío (0 bytes) -> 422
            res_empty = await client.post(
                "/api/v1/questionnaires/extract",
                files={"file": ("vacio.pdf", b"", "application/pdf")},
            )
            assert res_empty.status_code == 422
            assert res_empty.json()["code"] == "EMPTY_DOCUMENT"

            # 3. Archivo corrupto -> 422
            res_corrupt = await client.post(
                "/api/v1/questionnaires/extract",
                files={"file": ("corrupto.pdf", b"bytes-invalidos", "application/pdf")},
            )
            assert res_corrupt.status_code == 422
            assert res_corrupt.json()["code"] == "CORRUPTED_DOCUMENT"

            # 4. Documento sin ítems detectados por el LLM -> 422
            app.dependency_overrides[get_llm_extractor] = lambda: _FakeLLMExtractor(
                should_raise=NoItemsDetectedError("No items found.")
            )
            res_no_items = await client.post(
                "/api/v1/questionnaires/extract",
                files={"file": ("carta.docx", _make_docx_bytes("Carta formal"), "application/octet-stream")},
            )
            assert res_no_items.status_code == 422
            assert res_no_items.json()["code"] == "NO_ITEMS_DETECTED"
    finally:
        app.dependency_overrides.clear()


async def test_async_jobs_queue_and_worker_processing() -> None:
    """Verifica encolado multi-documento (202), procesamiento por worker y consulta por ID (200/404)."""
    test_queue = InMemoryJobQueue()
    test_parser = ParserService()
    test_llm = _FakeLLMExtractor()
    test_worker = ExtractionWorker(
        queue=test_queue,
        parser_service=test_parser,
        llm_extractor=test_llm,
    )

    app.dependency_overrides[get_job_queue] = lambda: test_queue
    app.dependency_overrides[get_parser_service] = lambda: test_parser
    app.dependency_overrides[get_llm_extractor] = lambda: test_llm

    worker_task = asyncio.create_task(test_worker.run_worker_loop())
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Encolar 2 documentos simultáneamente (.docx y .xlsx)
            enqueue_res = await client.post(
                "/api/v1/questionnaires/jobs",
                files=[
                    ("files", ("test_1.docx", _make_docx_bytes(), "application/octet-stream")),
                    ("files", ("test_2.xlsx", _make_xlsx_bytes(), "application/octet-stream")),
                ],
            )
            assert enqueue_res.status_code == 202
            jobs_data = enqueue_res.json()
            assert len(jobs_data) == 2

            # Esperar a que el worker procese la cola
            await asyncio.wait_for(test_queue._queue.join(), timeout=5.0)

            # 2. Consultar cada job por su job_id y verificar COMPLETED + resultado
            for created_job in jobs_data:
                job_id = created_job["job_id"]
                status_res = await client.get(f"/api/v1/questionnaires/jobs/{job_id}")
                assert status_res.status_code == 200
                job_payload = status_res.json()
                assert job_payload["status"] == "COMPLETED"
                assert job_payload["result"]["total_items"] == 2

            # 3. Consultar un job_id inexistente -> 404
            not_found_res = await client.get("/api/v1/questionnaires/jobs/non-existent-id")
            assert not_found_res.status_code == 404
    finally:
        worker_task.cancel()
        await asyncio.gather(worker_task, return_exceptions=True)
        app.dependency_overrides.clear()
