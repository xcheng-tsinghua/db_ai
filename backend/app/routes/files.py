import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel, Field
from backend.app.providers.manager import provider_manager
from backend.app.tools.file_agent import LocalFileAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["files"])

# --- Request Models for Local File Agent Operations ---

class FileReadRequest(BaseModel):
    filepath: str = Field(..., description="Relative path of the target file in the workspace")

class FileWriteRequest(BaseModel):
    filepath: str = Field(..., description="Relative path of the target file in the workspace")
    content: str = Field(..., description="Text content to write")
    dry_run: bool = Field(True, description="Enable dry-run preview (defaults to True)")

class FileModifyRequest(BaseModel):
    filepath: str = Field(..., description="Relative path of the target file in the workspace")
    find_str: str = Field(..., description="Content segment to search for")
    replace_str: str = Field(..., description="Content segment to replace matching text with")
    dry_run: bool = Field(True, description="Enable dry-run preview (defaults to True)")

class FileDeleteRequest(BaseModel):
    filepath: str = Field(..., description="Relative path of the target file in the workspace")
    dry_run: bool = Field(True, description="Enable dry-run preview (defaults to True)")

# --- 1. Remote Provider Files Endpoint (e.g. MiniMax storage) ---

@router.post("/upload")
async def upload_remote_file(file: UploadFile = File(...), purpose: str = Form("fine-tune")):
    """Uploads a file to the active model provider's remote storage."""
    provider_name = provider_manager.active_provider_name
    try:
        provider = provider_manager.active_provider
        content = await file.read()
        resp = await provider.upload_file(content, file.filename, purpose)
        if not resp["success"]:
            raise HTTPException(status_code=400, detail=resp["error"])
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Remote upload endpoint failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_remote_files(purpose: Optional[str] = "fine-tune"):
    """Lists files on the active model provider's remote storage."""
    try:
        provider = provider_manager.active_provider
        resp = await provider.list_files(purpose=purpose)
        if not resp["success"]:
            raise HTTPException(status_code=400, detail=resp["error"])
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Remote files listing failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{file_id}")
async def delete_remote_file(file_id: str):
    """Deletes a file on the active model provider's remote storage."""
    try:
        provider = provider_manager.active_provider
        resp = await provider.delete_file(file_id)
        if not resp["success"]:
            raise HTTPException(status_code=400, detail=resp["error"])
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Remote file deletion failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{file_id}")
async def download_remote_file(file_id: str):
    """Downloads content of a file stored in the active model provider's remote storage."""
    try:
        provider = provider_manager.active_provider
        resp = await provider.download_file(file_id)
        if not resp["success"]:
            raise HTTPException(status_code=400, detail=resp["error"])
        
        # Download responses may return file content binary stream directly
        if "file_content" in resp:
            return Response(content=resp["file_content"], media_type="application/octet-stream")
            
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Remote file download failed")
        raise HTTPException(status_code=500, detail=str(e))


# --- 2. Local File Safety Agent Endpoints ---

@router.get("/local/list")
async def list_local_directory(path: Optional[str] = ""):
    """Lists local files under the configured workspace root."""
    agent = LocalFileAgent()
    resp = agent.list_dir(path)
    if not resp["success"]:
        raise HTTPException(status_code=400, detail=resp["error"])
    return resp

@router.post("/local/read")
async def read_local_file(req: FileReadRequest):
    """Reads a local text file under the workspace root, applying safety checks."""
    agent = LocalFileAgent()
    resp = agent.read_file(req.filepath)
    if not resp["success"]:
        raise HTTPException(status_code=400, detail=resp["error"])
    return resp

@router.post("/local/write")
async def write_local_file(req: FileWriteRequest):
    """Writes/creates a local text file with automatic backup and dry-run preview."""
    agent = LocalFileAgent()
    resp = agent.write_file(req.filepath, req.content, dry_run=req.dry_run)
    if not resp["success"]:
        raise HTTPException(status_code=400, detail=resp["error"])
    return resp

@router.post("/local/modify")
async def modify_local_file(req: FileModifyRequest):
    """Modifies segments of a local text file with automatic backup and dry-run preview."""
    agent = LocalFileAgent()
    resp = agent.modify_file(req.filepath, req.find_str, req.replace_str, dry_run=req.dry_run)
    if not resp["success"]:
        raise HTTPException(status_code=400, detail=resp["error"])
    return resp

@router.post("/local/delete")
async def delete_local_file(req: FileDeleteRequest):
    """Deletes a local file/directory after copying a timestamped backup."""
    agent = LocalFileAgent()
    resp = agent.delete_file(req.filepath, dry_run=req.dry_run)
    if not resp["success"]:
        raise HTTPException(status_code=400, detail=resp["error"])
    return resp
