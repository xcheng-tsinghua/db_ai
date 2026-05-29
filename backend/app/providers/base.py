from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseModelProvider(ABC):
    """
    Abstract Base Class for all model providers.
    All methods return dicts containing standard fields:
    {
        "success": bool,
        "data": dict, # Response payload
        "error": str or None
    }
    """
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Send chat messages and get completion response."""
        pass

    @abstractmethod
    async def generate_image(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate an image from a text prompt."""
        pass

    @abstractmethod
    async def image_to_image(self, image_data: bytes, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate an image based on an existing image and a text prompt."""
        pass

    @abstractmethod
    async def generate_video(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate a video from a text prompt. For async APIs, returns a task_id."""
        pass

    @abstractmethod
    async def text_to_speech(self, text: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Convert text to speech audio."""
        pass

    @abstractmethod
    async def speech_to_text(self, audio_data: bytes, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Transcribe speech audio to text."""
        pass

    @abstractmethod
    async def generate_music(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate music from a text prompt. For async APIs, returns a task_id."""
        pass

    # File API Operations (primarily used by MiniMax or other agents for file grounding)
    @abstractmethod
    async def upload_file(self, file_content: bytes, filename: str, purpose: str = "fine-tune", **kwargs) -> Dict[str, Any]:
        """Upload a file to the provider's remote storage."""
        pass

    @abstractmethod
    async def list_files(self, **kwargs) -> Dict[str, Any]:
        """List uploaded files from the provider's remote storage."""
        pass

    @abstractmethod
    async def download_file(self, file_id: str, **kwargs) -> Dict[str, Any]:
        """Download a file's content from the provider's remote storage."""
        pass

    @abstractmethod
    async def delete_file(self, file_id: str, **kwargs) -> Dict[str, Any]:
        """Delete an uploaded file from the provider's remote storage."""
        pass
