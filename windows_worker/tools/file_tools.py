import os
from pydantic import BaseModel, Field
from windows_worker.config import settings
from windows_worker.tool_registry import registry, get_safe_path

class ListDirArgs(BaseModel):
    relative_path: str = Field(default=".", description="Relative path in the workspace directory to list.")

class ReadTextFileArgs(BaseModel):
    relative_path: str = Field(..., description="Relative path of the text file to read.")

class WriteTextFileArgs(BaseModel):
    relative_path: str = Field(..., description="Relative path of the text file to write.")
    content: str = Field(..., description="Content to write to the text file.")

@registry.register(
    name="list_dir",
    description="List the files and directories inside the specified relative path in the workspace.",
    parameter_schema=ListDirArgs
)
def list_dir(relative_path: str = "."):
    target_path = get_safe_path(relative_path)
    
    if not target_path.exists():
        raise FileNotFoundError(f"The path '{relative_path}' does not exist.")
        
    if not target_path.is_dir():
        raise NotADirectoryError(f"The path '{relative_path}' is not a directory.")
        
    items = []
    for item in os.scandir(target_path):
        # Resolve relative to workspace path
        rel_item_path = os.path.relpath(item.path, settings.WINDOWS_WORKSPACE_DIR)
        stat = item.stat()
        items.append({
            "name": item.name,
            "relative_path": rel_item_path,
            "is_dir": item.is_dir(),
            "is_file": item.is_file(),
            "size_bytes": stat.st_size if item.is_file() else None,
            "modified_time": stat.st_mtime
        })
        
    return {"relative_path": relative_path, "items": items}

@registry.register(
    name="read_text_file",
    description="Read the contents of a text file inside the workspace.",
    parameter_schema=ReadTextFileArgs
)
def read_text_file(relative_path: str):
    target_path = get_safe_path(relative_path)
    
    if not target_path.exists():
        raise FileNotFoundError(f"File '{relative_path}' does not exist.")
        
    if not target_path.is_file():
        raise IsADirectoryError(f"Path '{relative_path}' is a directory, not a file.")
        
    with open(target_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
        
    return {
        "relative_path": relative_path,
        "content": content,
        "size_bytes": len(content.encode("utf-8"))
    }

@registry.register(
    name="write_text_file",
    description="Create or overwrite a text file with specified content inside the workspace.",
    parameter_schema=WriteTextFileArgs
)
def write_text_file(relative_path: str, content: str):
    if not settings.ALLOW_FILE_WRITE:
        raise PermissionError("File modification is disabled on this worker (ALLOW_FILE_WRITE=false).")
        
    target_path = get_safe_path(relative_path)
    
    # Create parent directories safely
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return {
        "path": str(target_path),
        "bytes_written": len(content.encode("utf-8"))
    }
