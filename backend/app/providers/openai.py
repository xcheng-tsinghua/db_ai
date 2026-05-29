import logging
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from backend.app.providers.base import BaseModelProvider
from backend.app.config import settings

logger = logging.getLogger(__name__)

class OpenAICompatibleProvider(BaseModelProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.default_model = default_model or settings.OPENAI_DEFAULT_TEXT_MODEL
        
        # Lazily initialized to handle missing API keys gracefully at startup
        self._client: Optional[AsyncOpenAI] = None

    def get_client(self) -> AsyncOpenAI:
        if not self._client:
            if not self.api_key:
                raise ValueError("API key is not configured for OpenAI Compatible Provider.")
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    async def chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            client = self.get_client()
            target_model = model or self.default_model
            response = await client.chat.completions.create(
                model=target_model,
                messages=messages,
                **kwargs
            )
            return {
                "success": True,
                "data": response.model_dump(),
                "error": None
            }
        except Exception as e:
            logger.exception("OpenAI compatible chat failed")
            return {
                "success": False,
                "data": {},
                "error": f"OpenAI compatible chat error: {str(e)}"
            }

    async def generate_image(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            client = self.get_client()
            target_model = model or "dall-e-3"
            response = await client.images.generate(
                model=target_model,
                prompt=prompt,
                **kwargs
            )
            return {
                "success": True,
                "data": response.model_dump(),
                "error": None
            }
        except Exception as e:
            logger.exception("OpenAI compatible image generation failed")
            return {
                "success": False,
                "data": {},
                "error": f"OpenAI compatible image generation error: {str(e)}"
            }

    async def image_to_image(self, image_data: bytes, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            client = self.get_client()
            target_model = model or "dall-e-2"
            # OpenAI image edit needs file-like object
            response = await client.images.edit(
                image=image_data,
                prompt=prompt,
                model=target_model,
                **kwargs
            )
            return {
                "success": True,
                "data": response.model_dump(),
                "error": None
            }
        except Exception as e:
            logger.exception("OpenAI compatible image-to-image failed")
            return {
                "success": False,
                "data": {},
                "error": f"OpenAI compatible image-to-image error: {str(e)}"
            }

    async def generate_video(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        return {
            "success": False,
            "data": {},
            "error": "Video generation is not supported by standard OpenAI compatible endpoints."
        }

    async def text_to_speech(self, text: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            client = self.get_client()
            target_model = model or "tts-1"
            voice = kwargs.get("voice", "alloy")
            response = await client.audio.speech.create(
                model=target_model,
                voice=voice,
                input=text,
                response_format=kwargs.get("response_format", "mp3")
            )
            # Response content can be read synchronously or asynchronously, returning raw bytes
            audio_bytes = await response.aread()
            return {
                "success": True,
                "data": {"audio_base64_placeholder": True, "size_bytes": len(audio_bytes)},
                "audio_bytes": audio_bytes,
                "error": None
            }
        except Exception as e:
            logger.exception("OpenAI compatible speech synthesis failed")
            return {
                "success": False,
                "data": {},
                "error": f"OpenAI compatible text-to-speech error: {str(e)}"
            }

    async def speech_to_text(self, audio_data: bytes, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            client = self.get_client()
            target_model = model or "whisper-1"
            # Needs file-like object with name
            file_obj = ("speech.mp3", audio_data, "audio/mp3")
            response = await client.audio.transcriptions.create(
                file=file_obj,
                model=target_model,
                **kwargs
            )
            return {
                "success": True,
                "data": response.model_dump(),
                "error": None
            }
        except Exception as e:
            logger.exception("OpenAI compatible transcription failed")
            return {
                "success": False,
                "data": {},
                "error": f"OpenAI compatible speech-to-text error: {str(e)}"
            }

    async def generate_music(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        return {
            "success": False,
            "data": {},
            "error": "Music generation is not supported by standard OpenAI compatible endpoints."
        }

    async def query_task(self, task_id: str, task_type: str, **kwargs) -> Dict[str, Any]:
        return {
            "success": False,
            "data": {},
            "error": "Task status querying is not supported by standard OpenAI compatible endpoints."
        }

    # File API Operations
    async def upload_file(self, file_content: bytes, filename: str, purpose: str = "fine-tune", **kwargs) -> Dict[str, Any]:
        try:
            client = self.get_client()
            file_obj = (filename, file_content)
            response = await client.files.create(
                file=file_obj,
                purpose=purpose
            )
            return {
                "success": True,
                "data": response.model_dump(),
                "error": None
            }
        except Exception as e:
            logger.exception("OpenAI compatible file upload failed")
            return {
                "success": False,
                "data": {},
                "error": f"OpenAI compatible file upload error: {str(e)}"
            }

    async def list_files(self, **kwargs) -> Dict[str, Any]:
        try:
            client = self.get_client()
            response = await client.files.list(**kwargs)
            # Response is a SyncCursorPage of FileObjects
            files_list = [file.model_dump() for file in response.data]
            return {
                "success": True,
                "data": {"data": files_list},
                "error": None
            }
        except Exception as e:
            logger.exception("OpenAI compatible files listing failed")
            return {
                "success": False,
                "data": {},
                "error": f"OpenAI compatible list files error: {str(e)}"
            }

    async def download_file(self, file_id: str, **kwargs) -> Dict[str, Any]:
        try:
            client = self.get_client()
            content = await client.files.content(file_id)
            file_content = await content.aread()
            return {
                "success": True,
                "data": {"size_bytes": len(file_content)},
                "file_content": file_content,
                "error": None
            }
        except Exception as e:
            logger.exception("OpenAI compatible file download failed")
            return {
                "success": False,
                "data": {},
                "error": f"OpenAI compatible download file error: {str(e)}"
            }

    async def delete_file(self, file_id: str, **kwargs) -> Dict[str, Any]:
        try:
            client = self.get_client()
            response = await client.files.delete(file_id)
            return {
                "success": True,
                "data": response.model_dump(),
                "error": None
            }
        except Exception as e:
            logger.exception("OpenAI compatible file deletion failed")
            return {
                "success": False,
                "data": {},
                "error": f"OpenAI compatible delete file error: {str(e)}"
            }
