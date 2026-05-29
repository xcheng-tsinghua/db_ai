import logging
import json
import re
from datetime import datetime
from typing import Any, Dict, List
from backend.app.agent.state import AgentState
from backend.app.providers.manager import provider_manager
from backend.app.tools.file_agent import LocalFileAgent

logger = logging.getLogger(__name__)

def add_trace(state: AgentState, node_name: str, status: str, output: Any = None) -> List[Dict[str, Any]]:
    """Helper to append a structured trace event."""
    trace = list(state.get("trace", []))
    trace.append({
        "node": node_name,
        "status": status,
        "output": output,
        "timestamp": datetime.now().isoformat()
    })
    return trace

async def classify_task_node(state: AgentState) -> AgentState:
    """Classifies the user prompt using the active LLM or a rule-based fallback."""
    new_state = dict(state)
    new_state["trace"] = add_trace(new_state, "classify_task", "running")
    
    # Get last message text
    messages = new_state.get("messages", [])
    if not messages:
        new_state["task_type"] = "text"
        new_state["task_params"] = {}
        new_state["trace"] = add_trace(new_state, "classify_task", "completed", {"task_type": "text"})
        return new_state
        
    last_msg = messages[-1].get("content", "")
    
    # Define fallback rule classifier
    task_type = "text"
    params = {"prompt": last_msg}
    
    lower_msg = last_msg.lower()
    if any(k in lower_msg for k in ["generate image", "draw", "paint", "create picture", "make a picture", "image:"]):
        task_type = "image_generation"
        # Extract prompt
        cleaned = re.sub(r"(generate image|draw|paint|create picture|make a picture|image:)\s*", "", last_msg, flags=re.IGNORECASE)
        params["prompt"] = cleaned.strip()
    elif any(k in lower_msg for k in ["generate video", "create video", "make a video", "video:"]):
        task_type = "video_generation"
        cleaned = re.sub(r"(generate video|create video|make a video|video:)\s*", "", last_msg, flags=re.IGNORECASE)
        params["prompt"] = cleaned.strip()
    elif any(k in lower_msg for k in ["generate music", "create music", "make a song", "music:"]):
        task_type = "music_generation"
        cleaned = re.sub(r"(generate music|create music|make a song|music:)\s*", "", last_msg, flags=re.IGNORECASE)
        params["prompt"] = cleaned.strip()
    elif any(k in lower_msg for k in ["text to speech", "speak:", "read text", "tts:"]):
        task_type = "speech_synthesis"
        cleaned = re.sub(r"(text to speech|speak:|read text|tts:)\s*", "", last_msg, flags=re.IGNORECASE)
        params["prompt"] = cleaned.strip()
    elif any(k in lower_msg for k in ["read file", "write file", "modify file", "list dir", "delete file", "file:"]):
        task_type = "file_operation"
        # Extract action & file details
        if "read file" in lower_msg or "read:" in lower_msg:
            params["action"] = "read"
            params["filepath"] = re.sub(r"(read file|read:)\s*", "", last_msg, flags=re.IGNORECASE).strip()
        elif "list dir" in lower_msg:
            params["action"] = "list"
            params["filepath"] = re.sub(r"(list dir)\s*", "", last_msg, flags=re.IGNORECASE).strip()
        elif "delete file" in lower_msg:
            params["action"] = "delete"
            params["filepath"] = re.sub(r"(delete file)\s*", "", last_msg, flags=re.IGNORECASE).strip()
        elif "write file" in lower_msg or "write:" in lower_msg:
            params["action"] = "write"
            # Format expected: "write file <filename>: <content>"
            match = re.search(r"(?:write file|write:)\s*([^\s:]+)\s*:(.*)", last_msg, re.IGNORECASE | re.DOTALL)
            if match:
                params["filepath"] = match.group(1).strip()
                params["content"] = match.group(2).strip()
            else:
                params["filepath"] = "output.txt"
                params["content"] = last_msg
        elif "modify file" in lower_msg or "modify:" in lower_msg:
            params["action"] = "modify"
            # Format expected: "modify file <filename> find <find> replace <replace>"
            match = re.search(r"(?:modify file|modify:)\s*([^\s]+)\s*find\s+(.*?)\s+replace\s+(.*)", last_msg, re.IGNORECASE | re.DOTALL)
            if match:
                params["filepath"] = match.group(1).strip()
                params["find_str"] = match.group(2).strip()
                params["replace_str"] = match.group(3).strip()
            else:
                params["filepath"] = "output.txt"
                params["find_str"] = ""
                params["replace_str"] = ""

    # Try LLM classification if active provider is configured and available
    active_provider = provider_manager.active_provider
    provider_name = provider_manager.active_provider_name
    
    # We only run LLM classification if provider has API keys ready
    provider_info = provider_manager.get_available_providers().get(provider_name, {})
    if provider_info.get("is_configured"):
        system_prompt = (
            "You are a task classification assistant. Classify the user query into one of these task types:\n"
            "1. 'image_generation' - request to draw, paint, or make an image\n"
            "2. 'video_generation' - request to generate a video\n"
            "3. 'speech_synthesis' - request to convert text to speech/speak/read\n"
            "4. 'music_generation' - request to generate music or a song\n"
            "5. 'file_operation' - request to read, write, modify, delete, or list files/directories\n"
            "6. 'text' - general conversation, analysis, coding, etc.\n\n"
            "Return a raw JSON object and nothing else:\n"
            '{"task_type": "...", "params": {"prompt": "...", "filepath": "...", "action": "read/write/modify/delete/list", "content": "...", "find_str": "...", "replace_str": "..."}}'
        )
        
        try:
            llm_resp = await active_provider.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": last_msg}
            ])
            if llm_resp["success"]:
                # Parse JSON block
                choices = llm_resp["data"].get("choices", [])
                text = ""
                if choices:
                    text = choices[0].get("message", {}).get("content", "")
                elif "reply" in llm_resp["data"]:
                    text = llm_resp["data"]["reply"]
                
                # Strip markdown blocks if any
                clean_json = re.sub(r"```json|```", "", text).strip()
                parsed = json.loads(clean_json)
                if parsed.get("task_type"):
                    task_type = parsed["task_type"]
                    params = parsed.get("params", params)
                    logger.info(f"LLM Classification succeeded: {task_type}")
        except Exception as e:
            logger.warning(f"LLM task classification failed: {str(e)}. Falling back to rule classifier.")

    new_state["task_type"] = task_type
    new_state["task_params"] = params
    new_state["provider"] = provider_name
    new_state["trace"] = add_trace(new_state, "classify_task", "completed", {
        "task_type": task_type,
        "provider": provider_name,
        "params": params
    })
    return new_state

async def text_generation_node(state: AgentState) -> AgentState:
    """Executes a standard LLM chat completion."""
    new_state = dict(state)
    new_state["trace"] = add_trace(new_state, "text_generation", "running")
    
    active_provider = provider_manager.active_provider
    resp = await active_provider.chat(new_state["messages"])
    
    if resp["success"]:
        # Extract reply text
        choices = resp["data"].get("choices", [])
        reply = ""
        if choices:
            reply = choices[0].get("message", {}).get("content", "")
        elif "reply" in resp["data"]:
            reply = resp["data"]["reply"]
            
        new_state["output"] = {
            "text": reply,
            "raw_response": resp["data"]
        }
        new_state["trace"] = add_trace(new_state, "text_generation", "completed")
    else:
        new_state["error"] = resp["error"]
        new_state["trace"] = add_trace(new_state, "text_generation", "failed", resp["error"])
        
    return new_state

async def media_generation_node(state: AgentState) -> AgentState:
    """Executes media generation: image, video, speech, music."""
    new_state = dict(state)
    task_type = new_state["task_type"]
    params = new_state["task_params"]
    
    new_state["trace"] = add_trace(new_state, f"media_{task_type}", "running")
    
    active_provider = provider_manager.active_provider
    prompt = params.get("prompt", "")
    
    resp = None
    if task_type == "image_generation":
        resp = await active_provider.generate_image(prompt)
    elif task_type == "video_generation":
        resp = await active_provider.generate_video(prompt)
    elif task_type == "speech_synthesis":
        resp = await active_provider.text_to_speech(prompt)
    elif task_type == "music_generation":
        resp = await active_provider.generate_music(prompt)
        
    if resp and resp["success"]:
        new_state["output"] = {
            "task_type": task_type,
            "prompt": prompt,
            "data": resp["data"],
            # Check if task is async (returns task_id)
            "task_id": resp["data"].get("task_id") or resp["data"].get("generation_id") or resp["data"].get("base_resp", {}).get("task_id")
        }
        new_state["trace"] = add_trace(new_state, f"media_{task_type}", "completed", new_state["output"])
    else:
        err = resp["error"] if resp else "Unknown media generation error"
        new_state["error"] = err
        new_state["trace"] = add_trace(new_state, f"media_{task_type}", "failed", err)
        
    return new_state

async def file_operation_node(state: AgentState) -> AgentState:
    """Executes safe local file operations."""
    new_state = dict(state)
    params = new_state["task_params"]
    action = params.get("action", "read")
    filepath = params.get("filepath", "")
    
    new_state["trace"] = add_trace(new_state, "file_operation", "running", {
        "action": action,
        "filepath": filepath
    })
    
    agent = LocalFileAgent()
    resp = None
    
    # We default dry_run to True for safety if not explicitly provided as False
    dry_run = params.get("dry_run", True)
    
    if action == "list":
        resp = agent.list_dir(filepath)
    elif action == "read":
        resp = agent.read_file(filepath)
    elif action == "write":
        content = params.get("content", "")
        resp = agent.write_file(filepath, content, dry_run=dry_run)
    elif action == "modify":
        find_str = params.get("find_str", "")
        replace_str = params.get("replace_str", "")
        resp = agent.modify_file(filepath, find_str, replace_str, dry_run=dry_run)
    elif action == "delete":
        resp = agent.delete_file(filepath, dry_run=dry_run)
        
    if resp and resp["success"]:
        new_state["output"] = {
            "action": action,
            "filepath": filepath,
            "result": resp.get("data")
        }
        new_state["trace"] = add_trace(new_state, "file_operation", "completed", new_state["output"])
    else:
        err = resp["error"] if resp else f"Unsupported file action: {action}"
        new_state["error"] = err
        new_state["trace"] = add_trace(new_state, "file_operation", "failed", err)
        
    return new_state
