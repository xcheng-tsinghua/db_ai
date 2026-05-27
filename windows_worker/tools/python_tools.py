import sys
import subprocess
from typing import List, Optional
from pydantic import BaseModel, Field
from windows_worker.tool_registry import registry, get_safe_path

class RunPythonScriptArgs(BaseModel):
    relative_path: str = Field(..., description="Relative path in the workspace to the python script.")
    args: Optional[List[str]] = Field(default=None, description="List of arguments to pass to the script.")

@registry.register(
    name="run_python_script",
    description="Run a Python script inside the workspace. The script path must be relative and inside the workspace.",
    parameter_schema=RunPythonScriptArgs
)
def run_python_script(relative_path: str, args: Optional[List[str]] = None):
    # Verify file is inside the workspace and exists
    target_path = get_safe_path(relative_path)
    
    if not target_path.exists():
        raise FileNotFoundError(f"Python script '{relative_path}' does not exist.")
        
    if not target_path.is_file():
        raise IsADirectoryError(f"Path '{relative_path}' is a directory, not a file.")
        
    # Build execution command using sys.executable (current Python environment)
    cmd = [sys.executable, str(target_path)]
    if args:
        cmd.extend(args)
        
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(target_path.parent)
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired as e:
        return {
            "stdout": e.stdout or "",
            "stderr": f"Script timed out after 60 seconds. {e.stderr or ''}",
            "returncode": -1,
            "success": False
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Execution failed: {str(e)}",
            "returncode": -2,
            "success": False
        }
