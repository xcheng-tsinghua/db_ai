from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Qwen API Configuration
    QWEN_BASE_URL: str = "http://localhost:8001/v1"
    QWEN_API_KEY: str = "EMPTY"
    QWEN_MODEL: str = "qwen14b"
    QWEN_TEMPERATURE: float = 0.2
    QWEN_MAX_TOKENS: int = 2048
    LLM_REQUEST_TIMEOUT_SECONDS: float = 300.0

    # Default LLM Provider Settings
    DEFAULT_LLM_PROVIDER: str = "local_qwen"

    # Windows Agent Worker Configuration
    WINDOWS_WORKER_BASE_URL: str = "http://127.0.0.1:9100"
    ENABLE_WINDOWS_WORKER: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
