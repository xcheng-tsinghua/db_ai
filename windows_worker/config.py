import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class WorkerSettings(BaseSettings):
    # Worker Host and Port
    WINDOWS_WORKER_HOST: str = "127.0.0.1"
    WINDOWS_WORKER_PORT: int = 9100

    # Workspace directory sandbox limit
    WINDOWS_WORKSPACE_DIR: str = r"C:\ai_worker_workspace"

    # Security Feature Flags
    ALLOW_SHELL: bool = False
    ALLOW_FILE_WRITE: bool = True
    ALLOW_SCREENSHOT: bool = True
    ALLOW_BROWSER_OPEN: bool = True

    model_config = SettingsConfigDict(
        # Look for .env.windows file in the worker directory or parent directory
        env_file=os.path.join(os.path.dirname(__file__), ".env.windows"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = WorkerSettings()
