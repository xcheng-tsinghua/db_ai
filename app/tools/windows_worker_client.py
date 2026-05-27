import logging
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class WindowsWorkerClient:
    def __init__(self):
        self.base_url = settings.WINDOWS_WORKER_BASE_URL.rstrip("/")
        self.enabled = settings.ENABLE_WINDOWS_WORKER

    def _check_enabled(self):
        if not self.enabled:
            raise RuntimeError(
                "Windows Agent Worker is disabled. To use this functionality, please set "
                "ENABLE_WINDOWS_WORKER=true in your server's .env file."
            )

    async def get_health(self) -> Dict[str, Any]:
        self._check_enabled()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to check health of Windows Worker at {self.base_url}: {str(e)}")
                raise RuntimeError(f"Windows Worker is offline or unreachable: {str(e)}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        self._check_enabled()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/tools/list", timeout=5.0)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to fetch tools list from Windows Worker: {str(e)}")
                raise RuntimeError(f"Failed to connect to Windows Worker tool registry: {str(e)}")

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        self._check_enabled()
        payload = {
            "tool_name": tool_name,
            "arguments": arguments,
            "request_id": request_id
        }
        
        # High timeout (65 seconds) to allow Python scripts and PowerShell commands to complete
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/tools/execute",
                    json=payload,
                    timeout=65.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to execute tool '{tool_name}' on Windows Worker: {str(e)}")
                raise RuntimeError(f"Error during Windows Worker tool execution: {str(e)}")

# Global client singleton
worker_client = WindowsWorkerClient()
