import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.providers.manager import provider_manager
from backend.app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["settings"])

class ProviderSwitchRequest(BaseModel):
    provider: str = Field(..., description="Name of the provider to activate (minimax, openai_compatible, local_qwen)")

@router.get("/providers")
async def get_providers():
    """Lists all available model providers and their current configuration status."""
    try:
        return {
            "success": True,
            "data": provider_manager.get_available_providers(),
            "error": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/providers")
async def switch_provider(req: ProviderSwitchRequest):
    """Switches the active system model provider dynamically."""
    try:
        provider_manager.set_active_provider(req.provider)
        return {
            "success": True,
            "data": {
                "active_provider": provider_manager.active_provider_name,
                "message": f"Successfully switched to provider '{provider_manager.active_provider_name}'"
            },
            "error": None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/workspace")
async def get_workspace():
    """Returns the workspace root directory location for local file operations."""
    return {
        "success": True,
        "data": {
            "workspace_root": settings.FILE_WORKSPACE_ROOT,
            "size_limit_mb": settings.FILE_SIZE_LIMIT_MB
        },
        "error": None
    }
