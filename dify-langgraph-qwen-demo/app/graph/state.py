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
