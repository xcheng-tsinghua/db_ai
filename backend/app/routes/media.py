import logging
import base64
import os
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from backend.app.providers.manager import provider_manager
from backend.app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/media", tags=["media"])

class PromptRequest(BaseModel):
    prompt: str = Field(..., description="Prompt for media generation")
    model: Optional[str] = Field(None, description="Model overrides")
    provider: Optional[str] = Field(None, description="Force a specific provider")

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize to speech")
    model: Optional[str] = Field(None, description="Model overrides")
    voice_id: Optional[str] = Field(None, description="Voice setting identifier")
    provider: Optional[str] = Field(None, description="Force a specific provider")

class MediaResponse(BaseModel):
    success: bool
    provider: str
    task_type: str
    data: Dict[str, Any]
    error: Optional[str] = None

@router.post("/image-generation", response_model=MediaResponse)
async def generate_image(req: PromptRequest):
    provider_name = req.provider or provider_manager.active_provider_name
    try:
        provider = provider_manager.get_provider(provider_name)
        resp = await provider.generate_image(req.prompt, req.model)
        return MediaResponse(
            success=resp["success"],
            provider=provider_name,
            task_type="image_generation",
            data=resp["data"],
            error=resp["error"]
        )
    except Exception as e:
        logger.exception("Image generation API call failed")
        return MediaResponse(success=False, provider=provider_name, task_type="image_generation", data={}, error=str(e))

@router.post("/video-generation", response_model=MediaResponse)
async def generate_video(req: PromptRequest):
    provider_name = req.provider or provider_manager.active_provider_name
    try:
        provider = provider_manager.get_provider(provider_name)
        resp = await provider.generate_video(req.prompt, req.model)
        return MediaResponse(
            success=resp["success"],
            provider=provider_name,
            task_type="video_generation",
            data=resp["data"],
            error=resp["error"]
        )
    except Exception as e:
        logger.exception("Video generation API call failed")
        return MediaResponse(success=False, provider=provider_name, task_type="video_generation", data={}, error=str(e))

@router.post("/music-generation", response_model=MediaResponse)
async def generate_music(req: PromptRequest):
    provider_name = req.provider or provider_manager.active_provider_name
    try:
        provider = provider_manager.get_provider(provider_name)
        resp = await provider.generate_music(req.prompt, req.model)
        return MediaResponse(
            success=resp["success"],
            provider=provider_name,
            task_type="music_generation",
            data=resp["data"],
            error=resp["error"]
        )
    except Exception as e:
        logger.exception("Music generation API call failed")
        return MediaResponse(success=False, provider=provider_name, task_type="music_generation", data={}, error=str(e))

@router.post("/text-to-speech", response_model=MediaResponse)
async def generate_tts(req: TTSRequest):
    provider_name = req.provider or provider_manager.active_provider_name
    try:
        provider = provider_manager.get_provider(provider_name)
        kwargs = {}
        if req.voice_id:
            kwargs["voice_id"] = req.voice_id
            
        resp = await provider.text_to_speech(req.text, req.model, **kwargs)
        
        if resp["success"] and "audio_bytes" in resp:
            audio_bytes = resp["audio_bytes"]
            # Save a local copy in the workspace folder for grounding/history
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{timestamp}.mp3"
            filepath = os.path.join(settings.FILE_WORKSPACE_ROOT, filename)
            
            with open(filepath, "wb") as f:
                f.write(audio_bytes)
                
            # Base64 encode the audio to return to frontend directly
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            
            # Enrich return data
            resp["data"]["local_filename"] = filename
            resp["data"]["audio_base64"] = audio_b64
            
        return MediaResponse(
            success=resp["success"],
            provider=provider_name,
            task_type="speech_synthesis",
            data=resp["data"],
            error=resp["error"]
        )
    except Exception as e:
        logger.exception("Text to speech API call failed")
        return MediaResponse(success=False, provider=provider_name, task_type="speech_synthesis", data={}, error=str(e))

@router.get("/tasks/{provider}/{task_type}/{task_id}", response_model=MediaResponse)
async def get_task_status(provider: str, task_type: str, task_id: str):
    """Retrieves current status for an asynchronous generation task."""
    try:
        prov = provider_manager.get_provider(provider)
        resp = await prov.query_task(task_id, task_type)
        return MediaResponse(
            success=resp["success"],
            provider=provider,
            task_type=task_type,
            data=resp["data"],
            error=resp["error"]
        )
    except Exception as e:
        logger.exception("Task status query failed")
        return MediaResponse(success=False, provider=provider, task_type=task_type, data={}, error=str(e))
