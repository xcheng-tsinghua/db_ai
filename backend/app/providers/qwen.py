import logging
from backend.app.providers.openai import OpenAICompatibleProvider
from backend.app.config import settings

logger = logging.getLogger(__name__)

class LocalQwenProvider(OpenAICompatibleProvider):
    """
    Local Qwen Provider.
    Inherits OpenAI-compatible functionalities and overrides base URLs and keys for local setups (Ollama/vLLM).
    Since local APIs (like Ollama) do not require a valid OpenAI key, we provide a placeholder 'local' key.
    """
    def __init__(self):
        super().__init__(
            api_key="local-qwen-key",  # Local setups typically don't check keys
            base_url=settings.LOCAL_QWEN_BASE_URL,
            default_model=settings.LOCAL_QWEN_DEFAULT_MODEL
        )
