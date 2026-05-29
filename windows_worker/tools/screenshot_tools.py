from pydantic import BaseModel, Field
from PIL import ImageGrab
from windows_worker.config import settings
from windows_worker.tool_registry import registry, get_safe_path

class TakeScreenshotArgs(BaseModel):
    relative_path: str = Field(default="screenshot.png", description="Workspace relative path where the screenshot will be saved (e.g. screenshot.png).")

@registry.register(
    name="take_screenshot",
    description="Take a screenshot of the main monitor and save it to the specified workspace path.",
    parameter_schema=TakeScreenshotArgs
)
def take_screenshot(relative_path: str = "screenshot.png"):
    if not settings.ALLOW_SCREENSHOT:
        raise PermissionError("Screenshot capture is disabled on this worker (ALLOW_SCREENSHOT=false).")
        
    target_path = get_safe_path(relative_path)
    
    # Ensure parent directories exist
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Grab the screenshot from the primary monitor
    screenshot = ImageGrab.grab()
    
    # Save the screenshot
    screenshot.save(target_path)
    
    # Encode to base64
    import base64
    from io import BytesIO
    buffered = BytesIO()
    screenshot.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return {
        "path": str(target_path),
        "width": screenshot.width,
        "height": screenshot.height,
        "format": screenshot.format or "PNG",
        "image_base64": img_base64
    }
