import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Try loading .env from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, ".env"))

# Set page config
st.set_page_config(
    page_title="Dify + LangGraph + Qwen MVP Test UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS Injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Main Layout */
    .stApp {
        background-color: #0b0f19;
        color: #f5f5f7;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Gradient Title */
    .title-container {
        padding: 2rem 0;
        text-align: center;
    }
    .title-text {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subtitle-text {
        color: #9ca3af;
        font-size: 1.1rem;
        font-weight: 300;
    }
    
    /* Custom card panels */
    .custom-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        margin-bottom: 1.5rem;
    }
    
    .card-header {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #ffffff;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 0.5rem;
    }
    
    /* Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }
    .badge-review-needed {
        background-color: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.4);
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.1);
        animation: pulse 2s infinite;
    }
    .badge-review-ok {
        background-color: rgba(16, 185, 129, 0.15);
        color: #a7f3d0;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .badge-task-type {
        background-color: rgba(59, 130, 246, 0.15);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.4);
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
        }
    }
</style>
""", unsafe_allow_html=True)

# Title Container
st.markdown("""
<div class="title-container">
    <div class="title-text">🤖 Dify + LangGraph + Qwen MVP Test UI</div>
    <div class="subtitle-text">Multi-Agent Industrial Diagnostics Reasoning workflow demo</div>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown("### ⚙️ Connection Settings")
default_backend_url = os.getenv("AGENT_API_URL", "http://127.0.0.1:8000/agent/invoke")
backend_url = st.sidebar.text_input("FastAPI Endpoint URL", value=default_backend_url)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 System Status")

# Check backend health
try:
    health_url = backend_url.replace("/agent/invoke", "/health")
    health_response = requests.get(health_url, timeout=3)
    if health_response.status_code == 200:
        data = health_response.json()
        st.sidebar.success("Backend: ONLINE")
        st.sidebar.info(f"Served LLM: `{data.get('model_configured', 'unknown')}`")
    else:
        st.sidebar.warning(f"Backend Status: {health_response.status_code}")
except Exception:
    st.sidebar.error("Backend: OFFLINE")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ Help")
st.sidebar.write("This Web UI is for local MVP testing and debugging. Ensure the FastAPI application and the Qwen server are both active.")

# Session state initialization for prefilling text area
if "query_text" not in st.session_state:
    st.session_state.query_text = ""

example_query = "A batch of machined parts has an outer diameter deviation of +0.05mm. The machine is CNC-01, the material is 45 steel, and the cutting tool was recently replaced. Please analyze possible causes and provide troubleshooting steps."

# UI Layout columns (Input and Output)
col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.markdown('<div class="card-header">📝 User Prompt Input</div>', unsafe_allow_html=True)
    
    # Example loader button
    if st.button("✨ Load Quality Analysis Example Prompt", use_container_width=True):
        st.session_state.query_text = example_query
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()
            
    # Forms and parameter inputs
    with st.form("agent_invoke_form"):
        query = st.text_area(
            "Query Prompt",
            value=st.session_state.query_text,
            placeholder="Type your industrial query prompt here...",
            height=200
        )
        
        user_id = st.text_input("User ID", value="web_demo_user")
        
        submit_btn = st.form_submit_button("🚀 Invoke Agent Workflow", use_container_width=True)

# Process form submission
if submit_btn:
    if not query.strip():
        with col_output:
            st.warning("Please enter a query prompt before submitting.")
    else:
        with col_output:
            # Spinner loader
            with st.spinner("Invoking LangGraph Workflow... Querying Qwen..."):
                payload = {
                    "query": query,
                    "user_id": user_id,
                    "context": {}
                }
                
                try:
                    response = requests.post(backend_url, json=payload, timeout=120)
                    
                    if response.status_code == 200:
                        res_data = response.json()
                        answer = res_data.get("answer", "")
                        task_type = res_data.get("task_type", "unknown")
                        need_review = res_data.get("need_human_review", False)
                        agent_trace = res_data.get("agent_trace", [])
                        
                        # Style Badge Header Container
                        badge_html = f'<span class="badge badge-task-type">Task: {task_type.upper()}</span>'
                        if need_review:
                            badge_html += '<span class="badge badge-review-needed">⚠️ HUMAN REVIEW REQUIRED</span>'
                        else:
                            badge_html += '<span class="badge badge-review-ok">✅ STABLE: NO REVIEW NEEDED</span>'
                        
                        st.markdown(f"<div>{badge_html}</div><br>", unsafe_allow_html=True)
                        
                        # 1. Final Answer Card
                        st.markdown('<div class="card-header">📊 Final Diagnostic Report</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="custom-card">{answer}</div>', unsafe_allow_html=True)
                        
                        # 2. Agent Trace
                        st.markdown('<div class="card-header">🔍 Agent Workflow Execution Trace</div>', unsafe_allow_html=True)
                        if agent_trace:
                            for idx, step in enumerate(agent_trace):
                                step_num = idx + 1
                                agent_name = step.get("agent", "unknown").replace("_node", "").upper()
                                with st.expander(f"Step {step_num}: {agent_name} AGENT"):
                                    st.markdown("**Input Payload:**")
                                    st.code(step.get("input", ""))
                                    st.markdown("**Response Generated:**")
                                    st.code(step.get("output", ""))
                        else:
                            st.write("No trace items returned.")
                            
                        # 3. Raw Response
                        with st.expander("🛠️ Raw JSON Response (Developer Logs)"):
                            st.json(res_data)
                            
                    else:
                        st.error(f"Backend API Error (Status {response.status_code}): {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to agent backend. Please make sure FastAPI is running on port 8000.")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
else:
    with col_output:
        st.markdown('<div class="card-header">📈 Response & Diagnostic Output</div>', unsafe_allow_html=True)
        st.info("Submit a query prompt on the left to invoke the LangGraph reasoning workflow and view output steps.")
