# Developer Guide: Adding a Model Provider Adapter

This guide explains how to add support for a new model provider (e.g., Anthropic, Gemini, or a custom local adapter) in the project.

## Step 1: Implement the BaseModelProvider Interface

Create a new file under `backend/app/providers/` (e.g., `gemini.py`) and extend `BaseModelProvider` from `.base`:

```python
from backend.app.providers.base import BaseModelProvider
from typing import Any, Dict, List, Optional

class GeminiProvider(BaseModelProvider):
    def __init__(self):
        # Read API key from env or config file
        self.api_key = "..."
        
    async def chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        # Implement request using httpx or native SDK
        return {"success": True, "data": {"reply": "Hello!"}, "error": None}
        
    # Implement other abstract methods. 
    # Return {"success": False, "error": "Not supported"} for unsupported capabilities.
```

All return payloads must strictly follow the response dictionary shape:
```python
{
    "success": bool,
    "data": dict, # Response payload content
    "error": str or None # Description of failure if success is False
}
```

## Step 2: Register the Provider Class

Open `backend/app/providers/manager.py` and register the new class inside `ProviderManager.__init__`:

```python
from backend.app.providers.gemini import GeminiProvider # Import your class

class ProviderManager:
    def __init__(self):
        self._provider_classes: Dict[str, Type[BaseModelProvider]] = {
            "minimax": MiniMaxProvider,
            "openai_compatible": OpenAICompatibleProvider,
            "local_qwen": LocalQwenProvider,
            "gemini": GeminiProvider # Register here
        }
```

## Step 3: Add Environment Variables

Update `backend/app/config.py` to declare configuration settings if necessary:

```python
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_DEFAULT_TEXT_MODEL: str = "gemini-1.5-pro"
```

Then update `.env.example` and the frontend settings view to complete the configuration integration.
