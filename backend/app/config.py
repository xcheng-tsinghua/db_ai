import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "AI Agent Base"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # Default Active Provider (minimax, openai_compatible, local_qwen)
    ACTIVE_PROVIDER: str = "minimax"

    # MiniMax Configuration
    MINIMAX_API_KEY: Optional[str] = None
    MINIMAX_BASE_URL: str = "https://api.minimax.chat/v1"
    MINIMAX_DEFAULT_TEXT_MODEL: str = "abab6.5g-chat"
    MINIMAX_DEFAULT_IMAGE_MODEL: str = "abab-text-to-image"
    MINIMAX_DEFAULT_VIDEO_MODEL: str = "video-01"
    MINIMAX_DEFAULT_SPEECH_MODEL: str = "speech-01"
    MINIMAX_DEFAULT_MUSIC_MODEL: str = "music-01"

    # OpenAI-Compatible Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_DEFAULT_TEXT_MODEL: str = "gpt-4o-mini"

    # Local Qwen Configuration
    LOCAL_QWEN_BASE_URL: str = "http://localhost:11434/v1"  # Defaults to local Ollama/vLLM
    LOCAL_QWEN_DEFAULT_MODEL: str = "qwen2.5:7b"

    # Local File Agent Workspace Safety Rules
    # Default FILE_WORKSPACE_ROOT to the parent directory of this backend application
    FILE_WORKSPACE_ROOT: str = str(Path(__file__).resolve().parent.parent.parent.joinpath("workspace"))
    FILE_SIZE_LIMIT_MB: float = 10.0  # Limit files to 10MB by default

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings singleton
settings = Settings()

# Ensure that the workspace directory exists
os.makedirs(settings.FILE_WORKSPACE_ROOT, exist_ok=True)
