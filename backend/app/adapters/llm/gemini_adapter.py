from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.adapters.llm.prompts import QUESTIONNAIRE_SYSTEM_PROMPT, build_user_prompt
from app.domain.exceptions import LLMExtractionError, NoItemsDetectedError
from app.domain.ports import LLMExtractorPort
from app.domain.schemas import ItemType, QuestionnaireOutput


class _LLMAlternative(BaseModel):
    valor: str
    texto: str


class _LLMQuestionItem(BaseModel):
    numero: int
    enunciado: str
    tipo: ItemType
    alternativas: list[_LLMAlternative] = Field(default_factory=list)
    respuesta_correcta: str | None = None


class _LLMQuestionnaireResponse(BaseModel):
    titulo: str
    idioma: str
    items: list[_LLMQuestionItem] = Field(default_factory=list)


class GeminiExtractorAdapter(LLMExtractorPort):
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        client: genai.Client | None = None,
    ):
        if not api_key and client is None:
            self._client = None
        else:
            self._client = client or genai.Client(api_key=api_key)
        self._model_name = model_name

    async def extract_questionnaire(
        self, raw_text: str, filename: str
    ) -> QuestionnaireOutput:
        if not self._client:
            raise LLMExtractionError("No LLM Client")
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=build_user_prompt(raw_text, filename),
                config=types.GenerateContentConfig(
                    system_instruction=QUESTIONNAIRE_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=_LLMQuestionnaireResponse,
                    temperature=0.0,
                ),
            )
        except Exception as e:
            raise LLMExtractionError(f"Gemini extraction failed: {e}")
        if not response.text:
            raise LLMExtractionError("Empty response from Gemini.")
        try:
            llm_data = _LLMQuestionnaireResponse.model_validate_json(response.text)
        except Exception as e:
            raise LLMExtractionError("Unvalid format.")
        if not llm_data.items:
            raise NoItemsDetectedError(
                f"No questionnaire items were detected in '{filename}'."
            )
        return QuestionnaireOutput.model_validate(llm_data.model_dump())
