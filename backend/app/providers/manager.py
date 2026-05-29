import logging
from typing import Any, Dict, Optional, Type
from backend.app.providers.base import BaseModelProvider
from backend.app.providers.minimax import MiniMaxProvider
from backend.app.providers.openai import OpenAICompatibleProvider
from backend.app.providers.qwen import LocalQwenProvider
from backend.app.config import settings

logger = logging.getLogger(__name__)

class ProviderManager:
    def __init__(self):
        self._provider_classes: Dict[str, Type[BaseModelProvider]] = {
            "minimax": MiniMaxProvider,
            "openai_compatible": OpenAICompatibleProvider,
            "local_qwen": LocalQwenProvider
        }
        # Cache for instantiated provider objects (lazy loading)
        self._instances: Dict[str, BaseModelProvider] = {}
        # Track the active provider name
        self._active_provider_name: str = settings.ACTIVE_PROVIDER

    def get_provider(self, name: str) -> BaseModelProvider:
        """Retrieves and lazily instantiates a provider by name."""
        name = name.lower()
        if name not in self._provider_classes:
            raise ValueError(f"Unknown provider: {name}. Available: {list(self._provider_classes.keys())}")
        
        if name not in self._instances:
            logger.info(f"Lazily initializing model provider adapter: '{name}'")
            try:
                self._instances[name] = self._provider_classes[name]()
            except Exception as e:
                logger.error(f"Failed to instantiate provider '{name}': {str(e)}")
                raise RuntimeError(f"Could not load provider '{name}': {str(e)}") from e
                
        return self._instances[name]

    @property
    def active_provider(self) -> BaseModelProvider:
        """Gets the currently active model provider object."""
        return self.get_provider(self._active_provider_name)

    @property
    def active_provider_name(self) -> str:
        """Gets the name of the currently active model provider."""
        return self._active_provider_name

    def set_active_provider(self, name: str) -> None:
        """Sets the active provider. Validates name exists."""
        name = name.lower()
        if name not in self._provider_classes:
            raise ValueError(f"Unknown provider: {name}. Available: {list(self._provider_classes.keys())}")
        
        # Ensure we can load it successfully before switching
        _ = self.get_provider(name)
        
        logger.info(f"Switching active provider from '{self._active_provider_name}' to '{name}'")
        self._active_provider_name = name

    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Returns metadata about available providers, indicating if they are configured."""
        result = {}
        for name in self._provider_classes:
            is_configured = True
            missing_reason = None
            
            # Basic validation check for configs
            if name == "minimax" and not settings.MINIMAX_API_KEY:
                is_configured = False
                missing_reason = "MINIMAX_API_KEY environment variable is not set."
            elif name == "openai_compatible" and not settings.OPENAI_API_KEY:
                is_configured = False
                missing_reason = "OPENAI_API_KEY environment variable is not set."
                
            result[name] = {
                "name": name,
                "is_configured": is_configured,
                "missing_reason": missing_reason,
                "is_active": name == self._active_provider_name
            }
        return result

# Singleton manager
provider_manager = ProviderManager()
