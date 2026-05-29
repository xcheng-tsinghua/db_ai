from langgraph.graph import StateGraph, END
from backend.app.agent.state import AgentState
from backend.app.agent.nodes import (
    classify_task_node,
    text_generation_node,
    media_generation_node,
    file_operation_node
)

def route_task(state: AgentState) -> str:
    """Conditional router based on classified task type."""
    task_type = state.get("task_type", "text")
    
    if task_type == "text":
        return "text_generation"
    elif task_type in ["image_generation", "image_to_image", "video_generation", "speech_synthesis", "music_generation"]:
        return "media_generation"
    elif task_type == "file_operation":
        return "file_operation"
    else:
        return "text_generation"

# Initialize state graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("classify_task", classify_task_node)
workflow.add_node("text_generation", text_generation_node)
workflow.add_node("media_generation", media_generation_node)
workflow.add_node("file_operation", file_operation_node)

# Set entry point
workflow.set_entry_point("classify_task")

# Add conditional edges
workflow.add_conditional_edges(
    "classify_task",
    route_task,
    {
        "text_generation": "text_generation",
        "media_generation": "media_generation",
        "file_operation": "file_operation"
    }
)

# Connect execution nodes to the END node
workflow.add_edge("text_generation", END)
workflow.add_edge("media_generation", END)
workflow.add_edge("file_operation", END)

# Compile the workflow graph
agent_graph = workflow.compile()
