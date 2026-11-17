from typing import Protocol
from .schemas import QuestionnaireOutput, ExtractionJob


class DocumentParserPort(Protocol):
    """
    Protocol for a document parser that defines the interface for parsing
    document files.
    Methods:
        parse(file_bytes: bytes, filename: str) -> str:
            Parses the given file bytes and returns the parsed content as a string.
            Parameters:
                file_bytes (bytes): The raw bytes of the document to be parsed.
                filename (str): The name of the file being parsed, which may be used
                                for determining the file type or for error reporting.
            Returns:
                str: The parsed content of the document.
    """

    def parse(self, file_bytes: bytes, filename: str) -> str: ...


class LLMExtractorPort(Protocol):
    """
    Protocol for extracting questionnaire data from raw text.
    This protocol defines the method required to extract a questionnaire from
    a given raw text input and filename. Implementations of this protocol
    should provide the logic for processing the raw text and returning the
    structured questionnaire output.
    Methods:
        extract_questionnaire(raw_text: str, filename: str) -> QuestionnaireOutput:
            Asynchronously extracts a questionnaire from the provided raw text
            and filename, returning the structured output.
    """

    async def extract_questionnaire(
        self, raw_text: str, filename: str
    ) -> QuestionnaireOutput: ...


class JobQueuePort(Protocol):
    """
    JobQueuePort is a protocol that defines the interface for a job queue.
    This protocol requires the implementation of an asynchronous method to enqueue jobs.
    Methods:
        enqueue(job_id: str, filename: str, file_bytes: bytes) -> ExtractionJob:
            Enqueues a job with the specified job ID, filename, and file bytes.
            Returns an instance of ExtractionJob upon successful enqueueing.
    """

    async def enqueue(
        self, job_id: str, filename: str, file_bytes: bytes
    ) -> ExtractionJob: ...

    async def get_job(self, job_id: str) -> ExtractionJob | None: ...
