import logging
from typing import List
from fastapi import FastAPI, HTTPException
from windows_worker.config import settings
from windows_worker.schemas import ToolExecuteRequest, ToolExecuteResponse, ToolInfo
from windows_worker.tool_registry import registry
# Trigger registration by importing tools
import windows_worker.tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Windows Agent Worker API",
    description="FastAPI service running on Windows to execute local sandboxed tools",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    """
    Returns the health status, sandbox configuration, and safety permission overrides.
    """
    return {
        "status": "healthy",
        "workspace_dir": settings.WINDOWS_WORKSPACE_DIR,
        "allow_shell": settings.ALLOW_SHELL,
        "allow_file_write": settings.ALLOW_FILE_WRITE,
        "allow_screenshot": settings.ALLOW_SCREENSHOT,
        "allow_browser_open": settings.ALLOW_BROWSER_OPEN
    }

@app.post("/tools/list", response_model=List[ToolInfo])
def list_tools():
    """
    List all safe tools registered on the Windows host.
    """
    return registry.list_tools()

@app.post("/tools/execute", response_model=ToolExecuteResponse)
def execute_tool(request: ToolExecuteRequest):
    """
    Executes a registered tool under sandbox restrictions.
    """
    tool_name = request.tool_name
    arguments = request.arguments
    req_id = request.request_id
    
    logger.info(f"Executing tool '{tool_name}' (id: {req_id}) with args: {arguments}")
    
    tool_func = registry.get_tool(tool_name)
    if not tool_func:
        logger.warning(f"Execution request failed: tool '{tool_name}' is not registered.")
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' is not registered."
        )
        
    try:
        # Call tool with arguments unpacked
        result = tool_func(**arguments)
        logger.info(f"Successfully executed tool '{tool_name}'.")
        return ToolExecuteResponse(
            success=True,
            tool_name=tool_name,
            result=result,
            error=None,
            request_id=req_id
        )
    except Exception as e:
        logger.error(f"Error running tool '{tool_name}': {str(e)}")
        return ToolExecuteResponse(
            success=False,
            tool_name=tool_name,
            result=None,
            error=str(e),
            request_id=req_id
        )
