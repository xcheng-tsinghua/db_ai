import pytest
from backend.app.providers.manager import ProviderManager
from backend.app.providers.base import BaseModelProvider
from backend.app.providers.minimax import MiniMaxProvider
from backend.app.providers.openai import OpenAICompatibleProvider
from backend.app.providers.qwen import LocalQwenProvider

def test_provider_registry():
    manager = ProviderManager()
    
    # Check defaults
    assert manager.active_provider_name in ["minimax", "openai_compatible", "local_qwen"]
    
    # Check registration mappings
    assert "minimax" in manager._provider_classes
    assert "openai_compatible" in manager._provider_classes
    assert "local_qwen" in manager._provider_classes

def test_lazy_instantiation():
    manager = ProviderManager()
    
    # Shouldn't be instantiated yet
    assert "minimax" not in manager._instances
    
    # Trigger lazy load
    provider = manager.get_provider("minimax")
    assert isinstance(provider, MiniMaxProvider)
    assert "minimax" in manager._instances

def test_switch_provider():
    manager = ProviderManager()
    
    # Switch active provider
    manager.set_active_provider("local_qwen")
    assert manager.active_provider_name == "local_qwen"
    assert isinstance(manager.active_provider, LocalQwenProvider)
    
    with pytest.raises(ValueError):
        manager.set_active_provider("unknown_provider")
