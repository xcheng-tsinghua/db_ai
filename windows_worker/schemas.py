from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")
    request_id: Optional[str] = Field(None, description="Optional unique identifier for tracing requests")

class ToolExecuteResponse(BaseModel):
    success: bool = Field(..., description="Whether the tool completed successfully")
    tool_name: str = Field(..., description="Name of the tool executed")
    result: Optional[Any] = Field(None, description="The successful return output of the tool")
    error: Optional[str] = Field(None, description="Error message string if execution failed")
    request_id: Optional[str] = Field(None, description="The request tracking identifier")

class ToolInfo(BaseModel):
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of the tool functionality")
    parameters: Dict[str, Any] = Field(..., description="JSON Schema for arguments expected by the tool")
