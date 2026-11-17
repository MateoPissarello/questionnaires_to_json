import json
import pytest

from app.adapters.llm.gemini_adapter import GeminiExtractorAdapter
from app.domain.exceptions import LLMExtractionError, NoItemsDetectedError


class _FakeResponse:
    def __init__(self, text: str | None) -> None:
        self.text = text


class _FakeAsyncModels:
    def __init__(
        self,
        response_text: str | None = None,
        should_raise: Exception | None = None,
    ) -> None:
        self._response_text = response_text
        self._should_raise = should_raise
        self.last_call_kwargs: dict[str, object] = {}

    async def generate_content(self, **kwargs: object) -> _FakeResponse:
        self.last_call_kwargs = kwargs
        if self._should_raise is not None:
            raise self._should_raise
        return _FakeResponse(self._response_text)


class _FakeAioClient:
    def __init__(self, models: _FakeAsyncModels) -> None:
        self.models = models


class _FakeGenaiClient:
    def __init__(
        self,
        response_text: str | None = None,
        should_raise: Exception | None = None,
    ) -> None:
        self.aio = _FakeAioClient(_FakeAsyncModels(response_text, should_raise))


async def test_gemini_adapter_extracts_and_normalizes_questionnaire() -> None:
    """Verifica que el adaptador extraiga el JSON del LLM y normalice tipos (Likert str -> int)."""
    fake_llm_json = json.dumps(
        {
            "titulo": "Questionario di esempio",
            "idioma": "IT",
            "items": [
                {
                    "numero": 1,
                    "enunciado": "Mi preoccupo eccessivamente per cose di poca importanza.",
                    "tipo": "escala_likert",
                    "alternativas": [
                        {"valor": "0", "texto": "Mai"},
                        {"valor": "1", "texto": "A volte"},
                        {"valor": "2", "texto": "Spesso"},
                        {"valor": "3", "texto": "Sempre"},
                    ],
                    "respuesta_correcta": None,
                },
                {
                    "numero": 2,
                    "enunciado": "Quale numero completa la serie: 2, 4, 8, 16, ...?",
                    "tipo": "seleccion_multiple",
                    "alternativas": [
                        {"valor": "A", "texto": "18"},
                        {"valor": "B", "texto": "24"},
                        {"valor": "C", "texto": "32"},
                    ],
                    "respuesta_correcta": "C",
                },
                {
                    "numero": 3,
                    "enunciado": "Descriva una situazione recente in cui si è sentito sotto pressione.",
                    "tipo": "desarrollo",
                    "alternativas": [],
                    "respuesta_correcta": None,
                },
            ],
        }
    )

    fake_client = _FakeGenaiClient(response_text=fake_llm_json)
    adapter = GeminiExtractorAdapter(
        api_key="fake-key",
        model_name="gemini-2.5-flash",
        client=fake_client,  # type: ignore[arg-type]
    )

    result = await adapter.extract_questionnaire(
        raw_text="Texto extraído del cuestionario",
        filename="esempio.pdf",
    )

    assert result.titulo == "Questionario di esempio"
    assert result.idioma == "it"
    assert result.total_items == 3
    assert result.items[0].alternativas[0].valor == 0
    assert isinstance(result.items[0].alternativas[0].valor, int)
    assert result.items[1].respuesta_correcta == "C"
    assert result.items[2].alternativas == []


async def test_gemini_adapter_raises_no_items_detected_when_items_empty() -> None:
    """Verifica que si el LLM devuelve items=[], se lance NoItemsDetectedError."""
    empty_items_json = json.dumps(
        {
            "titulo": "Factura Comercial",
            "idioma": "es",
            "items": [],
        }
    )
    fake_client = _FakeGenaiClient(response_text=empty_items_json)
    adapter = GeminiExtractorAdapter(
        api_key="fake-key",
        client=fake_client,  # type: ignore[arg-type]
    )

    with pytest.raises(NoItemsDetectedError):
        await adapter.extract_questionnaire(
            raw_text="Factura #12345 - Total a pagar $500",
            filename="factura.pdf",
        )


async def test_gemini_adapter_raises_llm_extraction_error_on_failures() -> None:
    """Verifica que errores de API, respuesta vacía o falta de API key lancen LLMExtractionError."""
    # 1. Sin API key ni cliente inyectado
    adapter_no_key = GeminiExtractorAdapter(api_key="", client=None)
    with pytest.raises(LLMExtractionError):
        await adapter_no_key.extract_questionnaire("texto", "test.pdf")

    # 2. Excepción de red / cuota en el SDK de Gemini
    failing_client = _FakeGenaiClient(should_raise=RuntimeError("429 Quota Exceeded"))
    adapter_failing = GeminiExtractorAdapter(
        api_key="fake-key",
        client=failing_client,  # type: ignore[arg-type]
    )
    with pytest.raises(LLMExtractionError):
        await adapter_failing.extract_questionnaire("texto", "test.pdf")

    # 3. Respuesta vacía (response.text = None)
    empty_response_client = _FakeGenaiClient(response_text=None)
    adapter_empty = GeminiExtractorAdapter(
        api_key="fake-key",
        client=empty_response_client,  # type: ignore[arg-type]
    )
    with pytest.raises(LLMExtractionError):
        await adapter_empty.extract_questionnaire("texto", "test.pdf")

    # 4. Inicialización real del cliente cuando solo se pasa api_key
    real_init_adapter = GeminiExtractorAdapter(api_key="dummy-api-key")
    assert real_init_adapter._client is not None
