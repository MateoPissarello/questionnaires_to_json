from app.domain.ports import JobQueuePort
from app.domain.schemas import ExtractionJob, QuestionnaireOutput
from datetime import datetime, timezone
import asyncio


class InMemoryJobQueue(JobQueuePort):
    def __init__(self):
        self._queue: asyncio.Queue[tuple[str, str, bytes]] = asyncio.Queue()
        self._jobs: dict[str, ExtractionJob] = {}

    async def enqueue(
        self, job_id: str, filename: str, file_bytes: bytes
    ) -> ExtractionJob:
        job = ExtractionJob(
            job_id=job_id,
            filename=filename,
            status="QUEUED",
            created_at=datetime.now(timezone.utc),
        )
        self._jobs[job_id] = job
        await self._queue.put((job_id, filename, file_bytes))
        return job

    async def get_job(self, job_id: str) -> ExtractionJob | None:
        return self._jobs.get(job_id)

    async def dequeue(self) -> tuple[str, str, bytes]:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    def mark_processing(self, job_id: str) -> None:
        self._jobs[job_id].status = "PROCESSING"

    def mark_completed(self, job_id: str, result: QuestionnaireOutput) -> None:
        job = self._jobs[job_id]
        job.status = "COMPLETED"
        job.result = result
        job.completed_at = datetime.now(timezone.utc)
        self._jobs[job_id] = job

    def mark_failed(self, job_id: str, error: str) -> None:
        self._jobs[job_id].status = "FAILED"
        self._jobs[job_id].error = error
        self._jobs[job_id].completed_at = datetime.now(timezone.utc)
