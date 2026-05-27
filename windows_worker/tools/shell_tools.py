import subprocess
from pydantic import BaseModel, Field
from pathlib import Path
from windows_worker.config import settings
from windows_worker.tool_registry import registry

class RunPowershellCommandArgs(BaseModel):
    command: str = Field(..., description="PowerShell command string to run.")

@registry.register(
    name="run_powershell_command",
    description="Execute a PowerShell command (Requires ALLOW_SHELL=true). Runs inside the workspace directory.",
    parameter_schema=RunPowershellCommandArgs
)
def run_powershell_command(command: str):
    if not settings.ALLOW_SHELL:
        raise PermissionError(
            "PowerShell command execution is disabled on this worker (ALLOW_SHELL=false). "
            "Please enable ALLOW_SHELL=true in configuration if needed."
        )
        
    # Ensure workspace directory exists as run directory
    workspace_path = Path(settings.WINDOWS_WORKSPACE_DIR).resolve()
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run powershell with timeout to prevent hang
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(workspace_path)
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
            "stderr": f"Command timed out after 60 seconds. {e.stderr or ''}",
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
# Keep in mind, shell execution has powerful access. Ensure ALLOW_SHELL configuration is protected.
