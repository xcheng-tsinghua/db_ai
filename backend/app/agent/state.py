from typing import Any, Dict, List, TypedDict, Optional

class AgentState(TypedDict):
    # Input chat messages
    messages: List[Dict[str, Any]]
    
    # Selected provider for this task
    provider: str
    
    # Classified task type: 'text', 'image_generation', 'image_to_image', 'video_generation', 'speech_synthesis', 'music_generation', 'file_operation'
    task_type: str
    
    # Extracted parameters for generation or file tasks (e.g., prompt, filepath, search_query)
    task_params: Dict[str, Any]
    
    # Step-by-step execution trace log for frontend visual debuggers
    trace: List[Dict[str, Any]]
    
    # Final structured data response
    output: Optional[Dict[str, Any]]
    
    # Error message if any step failed
    error: Optional[str]
