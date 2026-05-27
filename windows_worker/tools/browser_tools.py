import webbrowser
from pydantic import BaseModel, Field
from windows_worker.config import settings
from windows_worker.tool_registry import registry

class OpenUrlArgs(BaseModel):
    url: str = Field(..., description="The HTTP or HTTPS URL to open in the default web browser.")

@registry.register(
    name="open_url",
    description="Open a URL inside the default system browser on the Windows host.",
    parameter_schema=OpenUrlArgs
)
def open_url(url: str):
    if not settings.ALLOW_BROWSER_OPEN:
        raise PermissionError("Browser opening is disabled on this worker (ALLOW_BROWSER_OPEN=false).")
        
    # Security validation on the URL to prevent opening arbitrary local files or scripts
    lower_url = url.lower().strip()
    if not (lower_url.startswith("http://") or lower_url.startswith("https://")):
        raise ValueError(
            "Security restriction: Only http:// or https:// URL schemes are allowed."
        )
        
    # Open URL
    success = webbrowser.open(url)
    
    return {
        "success": success,
        "message": f"Successfully requested opening of '{url}'" if success else f"Failed to open '{url}'"
    }
