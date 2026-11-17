class DomainError(Exception):
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        """
        Initialize a DomainError instance.
        Args:
            message (str): The error message describing the exception.
            code (str): An optional error code for categorizing the exception. Default is "DOMAIN_ERROR".
        """
        self.code = code
        self.message = message
        super().__init__(message)


class UnsupportedFileFormatError(DomainError):
    def __init__(self, message: str = "Unsupported file format."):
        """
        Initialize an UnsupportedFileFormatError instance.
        Args:
            message (str): The error message describing the exception. Default is "Unsupported file format.".
        """
        super().__init__(message, code="UNSUPPORTED_FILE_FORMAT")


class FileTooLargeError(DomainError):
    def __init__(self, message: str = "File size exceeds the maximum allowed limit."):
        """
        Initialize a FileTooLargeError instance.
        Args:
            message (str): The error message describing the exception. Default is "File size exceeds the maximum allowed limit.".
        """
        super().__init__(message, code="FILE_TOO_LARGE")


class CorruptedDocumentError(DomainError):
    def __init__(self, message: str = "The document is corrupt."):
        """
        Initialize a CorruptedDocumentError instance.
        Args:
            message (str): The error message describing the exception. Default is "The document is corrupt.".
        """
        super().__init__(message, code="CORRUPTED_DOCUMENT")


class EmptyDocumentError(DomainError):
    def __init__(self, message: str = "The document is empty."):
        """
        Initialize an EmptyDocumentError instance.
        Args:
            message (str): The error message describing the exception. Default is "The document is empty.".
        """
        super().__init__(message, code="EMPTY_DOCUMENT")


class NoItemsDetectedError(DomainError):
    def __init__(self, message: str = "No items detected in the document."):
        """
        Initialize a NoItemsDetectedError instance.
        Args:
            message (str): The error message describing the exception. Default is "No items detected in the document.".
        """
        super().__init__(message, code="NO_ITEMS_DETECTED")


class LLMExtractionError(DomainError):
    def __init__(self, message: str = "Error occurred during LLM extraction."):
        """
        Initialize an LLMExtractionError instance.
        Args:
            message (str): The error message describing the exception. Default is "Error occurred during LLM extraction.".
        """
        super().__init__(message, code="LLM_EXTRACTION_ERROR")
