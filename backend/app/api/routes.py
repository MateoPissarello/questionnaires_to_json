from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import status as status_codes
from app.api.dependencies import (
    JobQueueDep,
    ParserService,
    LLMExtractorDep,
    ParserServiceDep,
)
import asyncio
import uuid

from app.domain.schemas import ExtractionJob
from fastapi.exceptions import HTTPException

router = APIRouter(prefix="/api/v1/questionnaires", tags=["questionnaires"])


@router.post(path="/extract", status_code=status_codes.HTTP_200_OK)
async def extract_questionnaire(
    file: UploadFile, parser_service: ParserServiceDep, llm_extractor: LLMExtractorDep
):
    file_bytes = await file.read()
    filename = file.filename or "document"

    raw_text = await asyncio.to_thread(
        parser_service.parse_document, file_bytes, filename
    )
    return await llm_extractor.extract_questionnaire(raw_text, filename)


@router.post(path="/jobs", status_code=status_codes.HTTP_202_ACCEPTED)
async def create_extraction_jobs(
    files: list[UploadFile], parser_service: ParserServiceDep, queue: JobQueueDep
):
    validated_files: list[tuple[str, bytes]] = []
    for file in files:
        file_bytes = await file.read()
        filename = file.filename or "document"
        parser_service.validate_file(file_bytes, filename)
        validated_files.append((filename, file_bytes))

    created_jobs: list[ExtractionJob] = []
    for filename, file_bytes in validated_files:
        job = await queue.enqueue(
            job_id=str(uuid.uuid4()), filename=filename, file_bytes=file_bytes
        )
        created_jobs.append(job)
    return created_jobs


@router.get(path="/jobs/{job_id}", status_code=status_codes.HTTP_200_OK)
async def get_job_by_id(job_id: str, queue: JobQueueDep):
    job = await queue.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status_codes.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    return job
