import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.agent.graph import agent_graph
from backend.app.providers.manager import provider_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]] = Field(..., description="List of chat messages in format: [{'role': 'user', 'content': '...'}]")
    provider: Optional[str] = Field(None, description="Force a specific provider for this chat request")

class AgentResponse(BaseModel):
    success: bool
    provider: str
    task_type: str
    data: Dict[str, Any]
    trace: List[Dict[str, Any]]
    error: Optional[str] = None

@router.post("/chat", response_model=AgentResponse)
async def run_chat_agent(req: ChatRequest):
    """
    Executes the LangGraph agent workflow.
    Classifies the task, dynamically routes execution to LLM, media, or file tools,
    and returns a structured Dify-compatible JSON trace.
    """
    # 1. Update active provider if requested
    if req.provider:
        try:
            provider_manager.set_active_provider(req.provider)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to set provider '{req.provider}': {str(e)}")
            
    active_provider = provider_manager.active_provider_name
    logger.info(f"Running LangGraph agent using provider '{active_provider}'")
    
    # 2. Invoke LangGraph
    initial_state = {
        "messages": req.messages,
        "provider": active_provider,
        "task_type": "text",
        "task_params": {},
        "trace": [],
        "output": None,
        "error": None
    }
    
    try:
        final_state = await agent_graph.ainvoke(initial_state)
        
        # 3. Format response to match Dify rules
        success = final_state.get("error") is None
        
        return AgentResponse(
            success=success,
            provider=final_state.get("provider", active_provider),
            task_type=final_state.get("task_type", "text"),
            data=final_state.get("output") or {},
            trace=final_state.get("trace", []),
            error=final_state.get("error")
        )
    except Exception as e:
        logger.exception("LangGraph execution failed")
        return AgentResponse(
            success=False,
            provider=active_provider,
            task_type="error",
            data={},
            trace=initial_state["trace"] + [{"node": "system", "status": "failed", "output": str(e)}],
            error=f"LangGraph execution exception: {str(e)}"
        )
