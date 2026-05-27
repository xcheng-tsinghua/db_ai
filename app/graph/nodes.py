from typing import Dict, Any
from app.graph.state import AgentState
from app.qwen_client import qwen_client
from app.prompts.router_prompt import ROUTER_SYSTEM_PROMPT
from app.prompts.analysis_prompt import ANALYSIS_SYSTEM_PROMPT_MAP
from app.prompts.writer_prompt import WRITER_SYSTEM_PROMPT

def _get_llm_kwargs(state: AgentState) -> dict:
    kwargs = {}
    if "llm_base_url" in state and state["llm_base_url"] is not None:
        kwargs["base_url"] = state["llm_base_url"]
    if "llm_model" in state and state["llm_model"] is not None:
        kwargs["model"] = state["llm_model"]
    if "llm_api_key" in state and state["llm_api_key"] is not None:
        kwargs["api_key"] = state["llm_api_key"]
    if "llm_temperature" in state and state["llm_temperature"] is not None:
        kwargs["temperature"] = state["llm_temperature"]
    if "llm_max_tokens" in state and state["llm_max_tokens"] is not None:
        kwargs["max_tokens"] = state["llm_max_tokens"]
    return kwargs

def router_node(state: AgentState) -> Dict[str, Any]:
    query = state.get("query", "")
    
    messages = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]
    
    output = qwen_client.chat_completion(messages, **_get_llm_kwargs(state))
    
    # Post-process router output
    cleaned_output = output.strip().lower()
    valid_categories = ["quality_analysis", "document_qa", "general_chat"]
    
    task_type = "general_chat"
    for cat in valid_categories:
        if cat in cleaned_output:
            task_type = cat
            break
            
    trace = {
        "agent": "router",
        "input": query,
        "output": f"Task classified as: {task_type}. Original model output: {output}"
    }
    
    current_trace = state.get("agent_trace", [])
    new_trace = list(current_trace) + [trace]
    
    return {
        "task_type": task_type,
        "router_output": output,
        "agent_trace": new_trace
    }

def analysis_node(state: AgentState) -> Dict[str, Any]:
    task_type = state.get("task_type", "general_chat")
    query = state.get("query", "")
    
    system_prompt = ANALYSIS_SYSTEM_PROMPT_MAP.get(task_type, ANALYSIS_SYSTEM_PROMPT_MAP["general_chat"])
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    
    output = qwen_client.chat_completion(messages, **_get_llm_kwargs(state))
    
    # Conditional logic: flag quality_analysis for human review in this MVP
    need_human_review = False
    if task_type == "quality_analysis":
        need_human_review = True
        
    trace = {
        "agent": "analysis",
        "input": f"Task Type: {task_type} | Query: {query}",
        "output": output
    }
    
    current_trace = state.get("agent_trace", [])
    new_trace = list(current_trace) + [trace]
    
    return {
        "analysis_output": output,
        "need_human_review": need_human_review,
        "agent_trace": new_trace
    }

def writer_node(state: AgentState) -> Dict[str, Any]:
    analysis_output = state.get("analysis_output", "")
    query = state.get("query", "")
    task_type = state.get("task_type", "general_chat")
    
    # Send context details to the writer agent
    user_content = f"Task Type: {task_type}\nOriginal Query: {query}\n\nRaw Analysis:\n{analysis_output}"
    
    messages = [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
    
    output = qwen_client.chat_completion(messages, **_get_llm_kwargs(state))
    
    trace = {
        "agent": "writer",
        "input": f"Raw Analysis (length: {len(analysis_output)} chars)",
        "output": "Generated final structured report."
    }
    
    current_trace = state.get("agent_trace", [])
    new_trace = list(current_trace) + [trace]
    
    return {
        "final_answer": output,
        "agent_trace": new_trace
    }
