from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.dependencies import get_extraction_worker
from app.domain.exceptions import DomainError
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    worker = get_extraction_worker()
    worker_tasks = [
        asyncio.create_task(worker.run_worker_loop())
        for _ in range(settings.worker_concurrency)
    ]
    try:
        yield
    finally:
        for task in worker_tasks:
            task.cancel()
        await asyncio.gather(*worker_tasks, return_exceptions=True)


app = FastAPI(
    title="Giunti Questionnaire Extractor API", version="1.0.0", lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
STATUS_CODE_BY_ERROR: dict[str, int] = {
    "UNSUPPORTED_FILE_FORMAT": 400,
    "FILE_TOO_LARGE": 413,
    "CORRUPTED_DOCUMENT": 422,
    "EMPTY_DOCUMENT": 422,
    "NO_ITEMS_DETECTED": 422,
    "LLM_EXTRACTION_ERROR": 502,
}


@app.exception_handler(DomainError)
async def map_exceptions(request: Request, exc: DomainError) -> JSONResponse:
    status_code = STATUS_CODE_BY_ERROR.get(exc.code, 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "code": exc.code},
    )


app.include_router(router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
