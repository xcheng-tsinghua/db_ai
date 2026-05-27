import logging
from pathlib import Path
from typing import Callable, Dict, Any, Type, List
from pydantic import BaseModel
from windows_worker.config import settings
from windows_worker.schemas import ToolInfo

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_infos: Dict[str, ToolInfo] = {}

    def register(self, name: str, description: str, parameter_schema: Type[BaseModel] = None):
        """
        Decorator to register a tool function under a specific name and schema.
        """
        def decorator(func: Callable):
            self._tools[name] = func
            # Extract parameters JSON schema if a Pydantic model is supplied
            params = {}
            if parameter_schema:
                # Use model_json_schema in Pydantic v2
                params = parameter_schema.model_json_schema()
            
            self._tool_infos[name] = ToolInfo(
                name=name,
                description=description,
                parameters=params
            )
            logger.info(f"Registered tool: {name}")
            return func
        return decorator

    def get_tool(self, name: str) -> Callable:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolInfo]:
        return list(self._tool_infos.values())

# Global registry instance
registry = ToolRegistry()

def get_safe_path(relative_path: str) -> Path:
    """
    Validates and resolves a relative path to ensure it resides strictly within 
    the configured WINDOWS_WORKSPACE_DIR. Raises ValueError on path traversal, 
    absolute path, or containment violations.
    """
    workspace_dir = settings.WINDOWS_WORKSPACE_DIR
    if not workspace_dir:
        raise ValueError("WINDOWS_WORKSPACE_DIR config is empty.")
        
    workspace_path = Path(workspace_dir).resolve()
    
    # Reject paths that look absolute, have drives, or start with slashes/backslashes
    path_str = str(relative_path).strip()
    if path_str.startswith('/') or path_str.startswith('\\'):
        raise ValueError(
            f"Absolute path or leading slash violation: '{relative_path}' is not allowed. "
            "Paths must be relative and start without slashes."
        )
        
    p = Path(path_str)
    # Reject drive paths (e.g. C:), absolute paths, or double-dot traversal segments
    if p.is_absolute() or p.drive or any(part == '..' for part in p.parts):
        raise ValueError(
            f"Path traversal or absolute path violation: '{relative_path}' is not allowed. "
            "Paths must be relative and confined to the workspace."
        )
        
    # Resolve the combined path
    target_path = (workspace_path / p).resolve()
    
    # Verify target path begins with the workspace path
    try:
        target_path.relative_to(workspace_path)
    except ValueError:
        raise ValueError(
            f"Path containment violation: path '{relative_path}' resolves outside workspace '{workspace_dir}'"
        )
        
    return target_path
