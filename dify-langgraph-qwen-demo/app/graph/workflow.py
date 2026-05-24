from langgraph.graph import StateGraph, START, END
from app.graph.state import AgentState
from app.graph.nodes import router_node, analysis_node, writer_node

def create_workflow():
    # Initialize the graph with our state schema
    workflow = StateGraph(AgentState)
    
    # Add nodes to the graph
    workflow.add_node("router", router_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("writer", writer_node)
    
    # Define edges (linear workflow)
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "analysis")
    workflow.add_edge("analysis", "writer")
    workflow.add_edge("writer", END)
    
    # Compile the workflow
    compiled_app = workflow.compile()
    return compiled_app

# Compiled workflow instance
agent_workflow = create_workflow()
