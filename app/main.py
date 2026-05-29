import asyncio
import logging
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.schemas import AgentRequest, AgentResponse, AgentTraceItem, LLMTestRequest
from app.graph.workflow import agent_workflow
from app.minimax_image_client import generate_minimax_images
from app.multimodal import normalize_input_images, wants_image_output
from app.tools.windows_worker_client import worker_client

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dify-LangGraph-Qwen Demo API",
    description="FastAPI backend integrating LangGraph and Qwen for Dify HTTP Request Node",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "agent-server"
    }

@app.get("/health/llm")
async def check_default_llm_health():
    # Resolve default LLM parameters from settings
    base_url = settings.QWEN_BASE_URL
    model = settings.QWEN_MODEL
    api_key = settings.QWEN_API_KEY
    provider = settings.DEFAULT_LLM_PROVIDER
    
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        # Lightweight check
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            timeout=5.0
        )
        return {
            "status": "healthy",
            "provider": provider,
            "base_url": base_url,
            "model": model
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "provider": provider,
            "base_url": base_url,
            "model": model,
            "error": str(e)
        }

@app.post("/llm/test")
async def test_llm_connection(req: LLMTestRequest):
    # Mask key in logging
    masked_key = "None"
    if req.llm_api_key:
        if req.llm_api_key == "EMPTY":
            masked_key = "EMPTY"
        else:
            masked_key = req.llm_api_key[:4] + "..." if len(req.llm_api_key) > 4 else "..."
            
    logger.info(f"Testing LLM connection: provider={req.llm_provider}, base_url={req.llm_base_url}, model={req.llm_model}, key={masked_key}")
    
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url=req.llm_base_url,
            api_key=req.llm_api_key
        )
        client.chat.completions.create(
            model=req.llm_model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            timeout=5.0
        )
        return {"success": True, "message": "Connection successful."}
    except Exception as e:
        logger.warning(f"LLM test connection failed: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/worker/health")
async def get_worker_health():
    if not settings.ENABLE_WINDOWS_WORKER:
        raise HTTPException(
            status_code=400,
            detail="Windows Agent Worker is disabled. Enable it by setting ENABLE_WINDOWS_WORKER=true in configuration."
        )
    try:
        health_info = await worker_client.get_health()
        return health_info
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.post("/worker/tools/list")
async def list_worker_tools():
    if not settings.ENABLE_WINDOWS_WORKER:
        raise HTTPException(
            status_code=400,
            detail="Windows Agent Worker is disabled. Enable it by setting ENABLE_WINDOWS_WORKER=true in configuration."
        )
    try:
        tools = await worker_client.list_tools()
        return tools
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.post("/worker/tools/execute")
async def execute_worker_tool(request_payload: dict):
    if not settings.ENABLE_WINDOWS_WORKER:
        raise HTTPException(
            status_code=400,
            detail="Windows Agent Worker is disabled. Enable it by setting ENABLE_WINDOWS_WORKER=true in configuration."
        )
    tool_name = request_payload.get("tool_name")
    arguments = request_payload.get("arguments", {})
    request_id = request_payload.get("request_id")
    
    if not tool_name:
        raise HTTPException(status_code=400, detail="tool_name is a required field.")
        
    try:
        result = await worker_client.execute_tool(tool_name, arguments, request_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.post("/agent/invoke", response_model=AgentResponse)
async def invoke_agent(request: AgentRequest):
    logger.info(f"Received request from user={request.user_id} with query='{request.query[:100]}...'")
    
    # Extract optional dynamic LLM config overrides from context
    context = request.context or {}
    llm_provider = context.get("llm_provider", settings.DEFAULT_LLM_PROVIDER)
    
    # Resolve values based on selected provider and fallbacks
    llm_base_url = context.get("llm_base_url")
    llm_model = context.get("llm_model")
    llm_api_key = context.get("llm_api_key")
    
    if not llm_base_url:
        if llm_provider == "local_qwen":
            llm_base_url = settings.QWEN_BASE_URL
        elif llm_provider == "minimax":
            llm_base_url = settings.MINIMAX_BASE_URL
        else:
            llm_base_url = settings.QWEN_BASE_URL
            
    if not llm_model:
        if llm_provider == "local_qwen":
            llm_model = settings.QWEN_MODEL
        elif llm_provider == "minimax":
            llm_model = "MiniMax-M2.7-highspeed"
        else:
            llm_model = settings.QWEN_MODEL
            
    if llm_api_key is None:
        if llm_provider == "local_qwen":
            llm_api_key = settings.QWEN_API_KEY
        elif llm_provider == "minimax":
            # Will be validated below
            llm_api_key = None
        else:
            llm_api_key = settings.QWEN_API_KEY

    # Validate MiniMax API Key existence
    if llm_provider == "minimax" and not llm_api_key:
        logger.warning("Request rejected: MiniMax API key is missing.")
        return JSONResponse(
            status_code=400,
            content={"error": "MiniMax API key is required. Please enter your API key or choose Local Qwen."}
        )
        
    llm_temperature = context.get("llm_temperature", settings.QWEN_TEMPERATURE)
    llm_max_tokens = context.get("llm_max_tokens", settings.QWEN_MAX_TOKENS)
    resolved_context = dict(context)
    resolved_context.update(
        {
            "llm_provider": llm_provider,
            "llm_base_url": llm_base_url,
            "llm_model": llm_model,
            "llm_api_key": llm_api_key,
            "llm_temperature": llm_temperature,
            "llm_max_tokens": llm_max_tokens,
        }
    )
    
    # Mask API key in debug logs
    masked_key = "None"
    if llm_api_key:
        if llm_api_key == "EMPTY":
            masked_key = "EMPTY"
        else:
            masked_key = llm_api_key[:4] + "..." if len(llm_api_key) > 4 else "..."
            
    logger.info(
        f"Dynamic LLM override detected: provider={llm_provider}, base_url={llm_base_url}, model={llm_model}, key={masked_key}, "
        f"temp={llm_temperature}, max_tokens={llm_max_tokens}"
    )
    
    # Initialize state
    initial_state = {
        "query": request.query,
        "user_id": request.user_id,
        "context": resolved_context,
        "task_type": "general_chat",
        "router_output": "",
        "analysis_output": "",
        "final_answer": "",
        "agent_trace": [],
        "need_human_review": False,
        "output_images": [],
        "warnings": [],
        "llm_base_url": llm_base_url,
        "llm_model": llm_model,
        "llm_api_key": llm_api_key,
        "llm_temperature": llm_temperature,
        "llm_max_tokens": llm_max_tokens
    }
    
    try:
        # Invoke the LangGraph workflow
        started_at = time.perf_counter()
        result = await asyncio.to_thread(agent_workflow.invoke, initial_state)
        elapsed_seconds = time.perf_counter() - started_at
        
        # Build the structured trace items
        trace_items = []
        for trace in result.get("agent_trace", []):
            trace_items.append(AgentTraceItem(
                agent=trace.get("agent", "unknown"),
                input=trace.get("input", ""),
                output=trace.get("output", "")
            ))

        warnings = list(result.get("warnings", []))
        output_images = list(result.get("output_images", []))

        if wants_image_output(request.query, resolved_context):
            if llm_provider == "minimax":
                try:
                    output_images.extend(
                        generate_minimax_images(
                            api_key=llm_api_key,
                            prompt=resolved_context.get("output_image_prompt") or request.query,
                            input_images=normalize_input_images(resolved_context),
                            model=resolved_context.get("image_generation_model") or settings.MINIMAX_IMAGE_MODEL,
                            aspect_ratio=resolved_context.get("output_image_aspect_ratio", "1:1"),
                            n=int(resolved_context.get("output_image_count", 1)),
                            response_format=resolved_context.get("output_image_response_format", "base64"),
                            prompt_optimizer=bool(resolved_context.get("output_image_prompt_optimizer", True)),
                        )
                    )
                except Exception as image_error:
                    logger.warning("Image generation failed: %s", image_error)
                    warnings.append(f"Image generation failed: {image_error}")
            else:
                warnings.append(
                    "Image output was requested, but the selected provider does not have a configured image generation API."
                )
            
        response = AgentResponse(
            answer=result.get("final_answer", "Error: No final answer generated by workflow."),
            task_type=result.get("task_type", "general_chat"),
            agent_trace=trace_items,
            need_human_review=result.get("need_human_review", False),
            error=None,
            output_images=output_images,
            warnings=warnings
        )
        
        logger.info(
            f"Workflow completed successfully in {elapsed_seconds:.2f}s. "
            f"task_type={response.task_type}, need_human_review={response.need_human_review}"
        )
        return response
        
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}", exc_info=True)
        
        # Formulate structured response error
        if llm_provider == "local_qwen":
            error_msg = f"Local Qwen server call failed at {llm_base_url}. Details: {str(e)}"
        else:
            error_msg = f"Model provider '{llm_provider}' is not reachable at {llm_base_url}. Details: {str(e)}"
            
        return AgentResponse(
            answer="",
            task_type="error",
            agent_trace=[],
            need_human_review=True,
            error=error_msg,
            output_images=[],
            warnings=[]
        )
