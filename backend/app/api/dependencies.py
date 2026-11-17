from functools import lru_cache
from typing import Annotated
from fastapi import Depends

from app.adapters.llm.gemini_adapter import GeminiExtractorAdapter
from app.adapters.queue.memory_queue import InMemoryJobQueue
from app.config import get_settings
from app.domain.ports import LLMExtractorPort
from app.services.extraction_worker import ExtractionWorker
from app.services.parser_service import ParserService


@lru_cache
def get_parser_service() -> ParserService:
    settings = get_settings()
    return ParserService(max_file_size_bytes=settings.max_file_size_bytes)


@lru_cache
def get_llm_extractor() -> LLMExtractorPort:
    settings = get_settings()
    return GeminiExtractorAdapter(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model,
    )


@lru_cache
def get_job_queue() -> InMemoryJobQueue:
    return InMemoryJobQueue()


@lru_cache
def get_extraction_worker() -> ExtractionWorker:
    return ExtractionWorker(
        queue=get_job_queue(),
        parser_service=get_parser_service(),
        llm_extractor=get_llm_extractor(),
    )


ParserServiceDep = Annotated[ParserService, Depends(get_parser_service)]
LLMExtractorDep = Annotated[LLMExtractorPort, Depends(get_llm_extractor)]
JobQueueDep = Annotated[InMemoryJobQueue, Depends(get_job_queue)]
ExtractionWorkerDep = Annotated[ExtractionWorker, Depends(get_extraction_worker)]
