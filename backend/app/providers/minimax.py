import logging
import json
from typing import Any, Dict, List, Optional
import httpx
from backend.app.providers.base import BaseModelProvider
from backend.app.config import settings

logger = logging.getLogger(__name__)

class MiniMaxProvider(BaseModelProvider):
    def __init__(self):
        self.api_key = settings.MINIMAX_API_KEY
        self.base_url = settings.MINIMAX_BASE_URL
        
    def _headers(self, is_multipart: bool = False) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key or ''}"
        }
        if not is_multipart:
            headers["Content-Type"] = "application/json"
        return headers

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "success": False,
                "data": {},
                "error": "MiniMax API key is not configured. Please add MINIMAX_API_KEY in your env settings."
            }
        
        url = f"{self.base_url.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                if method.upper() == "POST":
                    response = await client.post(url, **kwargs)
                elif method.upper() == "GET":
                    response = await client.get(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response_data = response.json()
                if response.status_code >= 400:
                    error_msg = response_data.get("base_resp", {}).get("status_msg") or response_data.get("error", {}).get("message") or response.text
                    return {
                        "success": False,
                        "data": response_data,
                        "error": f"MiniMax API returned error (HTTP {response.status_code}): {error_msg}"
                    }
                
                # MiniMax sometimes returns errors inside a 200 OK with 'base_resp'
                base_resp = response_data.get("base_resp", {})
                if base_resp and base_resp.get("status_code", 0) != 0:
                    return {
                        "success": False,
                        "data": response_data,
                        "error": f"MiniMax error (code {base_resp.get('status_code')}): {base_resp.get('status_msg')}"
                    }
                
                return {
                    "success": True,
                    "data": response_data,
                    "error": None
                }
            except Exception as e:
                logger.exception("MiniMax API Request failed")
                return {
                    "success": False,
                    "data": {},
                    "error": f"MiniMax request error: {str(e)}"
                }

    async def chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        payload = {
            "model": model or settings.MINIMAX_DEFAULT_TEXT_MODEL,
            "messages": messages,
            **kwargs
        }
        # MiniMax chat completion v2 endpoint
        return await self._request("POST", "/text/chatcompletion_v2", json=payload, headers=self._headers())

    async def generate_image(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        payload = {
            "model": model or settings.MINIMAX_DEFAULT_IMAGE_MODEL,
            "prompt": prompt,
            **kwargs
        }
        # MiniMax image generation endpoint
        return await self._request("POST", "/image_generation", json=payload, headers=self._headers())

    async def image_to_image(self, image_data: bytes, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        # Upload the image first to MiniMax Files API
        upload_resp = await self.upload_file(image_data, "image_to_image_ref.png", purpose="image_to_image")
        if not upload_resp["success"]:
            return upload_resp
            
        file_id = upload_resp["data"].get("file", {}).get("file_id") or upload_resp["data"].get("file_id")
        if not file_id:
            return {
                "success": False,
                "data": upload_resp["data"],
                "error": "Failed to retrieve file_id after image upload."
            }
            
        # Call image_generation with prompt and uploaded image reference
        payload = {
            "model": model or settings.MINIMAX_DEFAULT_IMAGE_MODEL,
            "prompt": prompt,
            "ref_image_id": file_id,
            **kwargs
        }
        return await self._request("POST", "/image_generation", json=payload, headers=self._headers())

    async def generate_video(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        payload = {
            "model": model or settings.MINIMAX_DEFAULT_VIDEO_MODEL,
            "prompt": prompt,
            **kwargs
        }
        # MiniMax video generation task creation endpoint
        return await self._request("POST", "/video_generation", json=payload, headers=self._headers())

    async def text_to_speech(self, text: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        # TODO: Confirm voice parameters for MiniMax TTS in detail if user requires custom voices
        payload = {
            "model": model or settings.MINIMAX_DEFAULT_SPEECH_MODEL,
            "text": text,
            "voice_setting": {
                "voice_id": kwargs.get("voice_id", "male-qn-reading"),
                "speed": kwargs.get("speed", 1.0),
                "vol": kwargs.get("vol", 1.0),
                "pitch": kwargs.get("pitch", 0)
            },
            **kwargs
        }
        return await self._request("POST", "/text_to_speech", json=payload, headers=self._headers())

    async def speech_to_text(self, audio_data: bytes, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        # Speech to text can upload file first or call synchronous speech to text endpoint
        # For simplicity, we implement a TODO check and default mock/placeholder response
        # TODO: Implement Speech-to-text when required by model compatibility
        return {
            "success": False,
            "data": {},
            "error": "Speech-to-Text is not fully implemented on MiniMax provider yet. File upload is required."
        }

    async def generate_music(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        payload = {
            "model": model or settings.MINIMAX_DEFAULT_MUSIC_MODEL,
            "prompt": prompt,
            **kwargs
        }
        return await self._request("POST", "/music_generation", json=payload, headers=self._headers())

    async def query_task(self, task_id: str, task_type: str, **kwargs) -> Dict[str, Any]:
        """Query task status for asynchronous jobs like video or music generation."""
        if task_type == "video":
            path = f"/query/video_generation?task_id={task_id}"
        elif task_type == "music":
            path = f"/query/music_generation?task_id={task_id}"
        else:
            return {
                "success": False,
                "data": {},
                "error": f"Unsupported task type for status query: {task_type}"
            }
        return await self._request("GET", path, headers=self._headers())

    # File API Operations
    async def upload_file(self, file_content: bytes, filename: str, purpose: str = "fine-tune", **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "success": False,
                "data": {},
                "error": "MiniMax API key is not configured."
            }
            
        url = f"{self.base_url.rstrip('/')}/files/upload"
        files = {
            "file": (filename, file_content)
        }
        data = {
            "purpose": purpose
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    url,
                    headers=self._headers(is_multipart=True),
                    files=files,
                    data=data
                )
                response_data = response.json()
                base_resp = response_data.get("base_resp", {})
                if base_resp and base_resp.get("status_code", 0) != 0:
                    return {
                        "success": False,
                        "data": response_data,
                        "error": base_resp.get("status_msg")
                    }
                
                return {
                    "success": True,
                    "data": response_data,
                    "error": None
                }
            except Exception as e:
                logger.exception("MiniMax File upload failed")
                return {
                    "success": False,
                    "data": {},
                    "error": f"MiniMax file upload error: {str(e)}"
                }

    async def list_files(self, **kwargs) -> Dict[str, Any]:
        # Query files by purpose
        purpose = kwargs.get("purpose", "fine-tune")
        return await self._request("GET", f"/files/list?purpose={purpose}", headers=self._headers())

    async def download_file(self, file_id: str, **kwargs) -> Dict[str, Any]:
        # Downloads binary content or metadata url
        return await self._request("GET", f"/files/retrieve_content?file_id={file_id}", headers=self._headers())

    async def delete_file(self, file_id: str, **kwargs) -> Dict[str, Any]:
        # MiniMax deletes files via POST `/files/delete` with file_id in JSON
        payload = {"file_id": file_id}
        return await self._request("POST", "/files/delete", json=payload, headers=self._headers())
