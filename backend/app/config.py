from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings class for application configuration.
    Attributes:
        app_env (str): The environment in which the application is running. Default is 'development'.
        gemini_api_key (str): The API key for accessing the Gemini service.
        gemini_model (str): The model name used for the Gemini service.
        max_file_size_mb (int): The maximum allowed file size in megabytes. Default is 20 MB.
        worker_concurrency (int): The number of concurrent workers for processing tasks. Default is 3.
    """

    app_env: str = "development"
    gemini_api_key: str = "gemini_api_key"
    gemini_model: str = "gemini-3.5-flash-lite"
    max_file_size_mb: int = 20
    worker_concurrency: int = 3

    @property
    def max_file_size_bytes(self) -> int:
        """
        Calculate the maximum file size in bytes based on the max_file_size_mb attribute.
        Returns:
            int: The maximum file size in bytes.
        """
        return self.max_file_size_mb * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> "Settings":
    """
    Get the application settings, cached for performance.
    Returns:
        Settings: An instance of the Settings class with the current configuration.
    """
    return Settings()
