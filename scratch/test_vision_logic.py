import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.multimodal import provider_supports_vision

def test_provider_supports_vision():
    # Test cases for Local Qwen
    # Case 1: Text-only model without explicit vision support
    assert provider_supports_vision("local_qwen", "qwen7b", {"llm_supports_vision": False}) is False
    assert provider_supports_vision("local_qwen", "qwen7b", {}) is False

    # Case 2: Vision model with auto detection or explicit setting
    assert provider_supports_vision("local_qwen", "qwen-vl", {}) is True
    assert provider_supports_vision("local_qwen", "qwen7b", {"llm_supports_vision": True}) is True

    # Test cases for MiniMax
    # Case 1: Default text-only model
    assert provider_supports_vision("minimax", "MiniMax-M2.7-highspeed", {"llm_supports_vision": False}) is False
    assert provider_supports_vision("minimax", "MiniMax-M2.7-highspeed", {}) is False

    # Case 2: Vision model with explicit check/setting or name matching
    assert provider_supports_vision("minimax", "MiniMax-VL-01", {}) is True
    assert provider_supports_vision("minimax", "MiniMax-M2.7-highspeed", {"llm_supports_vision": True}) is True

    print("All vision support validation tests passed successfully!")

if __name__ == "__main__":
    test_provider_supports_vision()
