from app.adapters.queue.memory_queue import InMemoryJobQueue
from app.domain.ports import LLMExtractorPort
from app.domain.schemas import ExtractionJob
from app.services.parser_service import ParserService
import asyncio


class ExtractionWorker:
    def __init__(
        self,
        queue: InMemoryJobQueue,
        parser_service: ParserService,
        llm_extractor: LLMExtractorPort,
    ):
        self._queue = queue
        self._parser_service = parser_service
        self._llm_extractor = llm_extractor

    async def process_job(
        self, job_id: str, filename: str, file_bytes: bytes
    ) -> ExtractionJob | None:
        self._queue.mark_processing(job_id=job_id)
        try:
            raw_text = await asyncio.to_thread(
                self._parser_service.parse_document, file_bytes, filename
            )
            result = await self._llm_extractor.extract_questionnaire(raw_text, filename)
            self._queue.mark_completed(job_id, result)
        except Exception as e:
            self._queue.mark_failed(job_id, str(e))
        return await self._queue.get_job(job_id)

    async def run_worker_loop(self) -> None:
        while True:
            job_id, filename, file_bytes = await self._queue.dequeue()
            try:
                await self.process_job(job_id, filename, file_bytes)
            finally:
                self._queue.task_done()
