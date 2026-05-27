from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    query: str
    user_id: str
    context: Dict[str, Any]
    task_type: str
    router_output: str
    analysis_output: str
    final_answer: str
    agent_trace: List[Dict[str, str]]
    need_human_review: bool
    llm_base_url: str
    llm_model: str
    llm_api_key: str
    llm_temperature: float
    llm_max_tokens: int
