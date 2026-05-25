import os
import requests
import datetime
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

# Custom High-Contrast Premium CSS Injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Main Layout */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Global Text Contrast Overrides */
    p, li, label, .stMarkdown {
        color: #f8fafc !important;
        font-size: 1.05rem !important;
        line-height: 1.6 !important;
    }
    
    /* Gradient Title */
    .title-container {
        padding: 1.5rem 0;
        text-align: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 2rem;
    }
    .title-text {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subtitle-text {
        color: #cbd5e1;
        font-size: 1.2rem;
        font-weight: 400;
    }
    
    /* Section Headers */
    .card-header {
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 1rem;
        margin-bottom: 1.25rem;
        color: #3b82f6;
        border-bottom: 2px solid rgba(59, 130, 246, 0.4);
        padding-bottom: 0.5rem;
        letter-spacing: 0.02em;
    }
    
    /* Inputs Styling Overrides for Contrast */
    .stTextArea textarea {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        font-size: 1.1rem !important;
        line-height: 1.5 !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
    }

    .stTextInput input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        font-size: 1.1rem !important;
    }
    
    .stTextInput input:focus {
        border-color: #3b82f6 !important;
    }
    
    /* Make Action Buttons Pop */
    div.stButton > button:first-child {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        border: 2px solid #2563eb !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    div.stButton > button:first-child:hover {
        background-color: #2563eb !important;
        border-color: #1d4ed8 !important;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    /* High-contrast Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.6rem 1.2rem;
        font-weight: 700;
        border-radius: 8px;
        font-size: 0.9rem;
        margin-right: 0.75rem;
        letter-spacing: 0.05em;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .badge-review-needed {
        background-color: #ef4444 !important;
        color: #ffffff !important;
        border: 1px solid #b91c1c !important;
        animation: pulse 2s infinite;
    }
    .badge-review-ok {
        background-color: #10b981 !important;
        color: #ffffff !important;
        border: 1px solid #047857 !important;
    }
    .badge-task-type {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        border: 1px solid #1d4ed8 !important;
    }
    
    /* Expander Panels High-Contrast styling */
    .streamlit-expanderHeader {
        background-color: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #f8fafc !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        margin-bottom: 0.25rem !important;
    }
    
    .streamlit-expanderContent {
        background-color: #0f172a !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-top: none !important;
        padding: 1.25rem !important;
        border-bottom-left-radius: 8px !important;
        border-bottom-right-radius: 8px !important;
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6);
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

# Title Header
st.markdown("""
<div class="title-container">
    <div class="title-text">🤖 Dify + LangGraph + Qwen MVP Test UI</div>
    <div class="subtitle-text">Multi-Agent Diagnostics Reasoning Workflow Demonstration</div>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration (Enhanced with System Diagnostics)
st.sidebar.markdown("### ⚙️ Connection Settings")
default_backend_url = os.getenv("AGENT_API_URL", "http://127.0.0.1:8000/agent/invoke")
backend_url = st.sidebar.text_input("FastAPI Endpoint URL", value=default_backend_url)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 System Status")

# Add live timestamp
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.sidebar.markdown(f"**Time Checked**: `{current_time}`")

# Check backend health
try:
    health_url = backend_url.replace("/agent/invoke", "/health")
    health_response = requests.get(health_url, timeout=3)
    if health_response.status_code == 200:
        data = health_response.json()
        st.sidebar.markdown("**Backend Health**: ✅ `ONLINE`")
        st.sidebar.markdown(f"**Served LLM**: `{data.get('model_configured', 'unknown')}`")
        st.sidebar.markdown(f"**API Base URL**: `{data.get('base_url', 'unknown')}`")
    else:
        st.sidebar.markdown(f"**Backend Health**: ⚠️ `STATUS {health_response.status_code}`")
except Exception:
    st.sidebar.markdown("**Backend Health**: ❌ `OFFLINE`")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🖥️ System Info")
st.sidebar.markdown("- **Host Mode**: Remote Server")
st.sidebar.markdown("- **Framework**: FastAPI + LangGraph")
st.sidebar.markdown("- **UI Engine**: Streamlit v1.27+")
st.sidebar.markdown("- **Target Device**: NVIDIA GPU (RTX 4090)")

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
            with st.spinner("Invoking LangGraph Workflow... Calling local Qwen..."):
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
                        
                        # Use success/warning alert panels for high contrast markdown rendering
                        if need_review:
                            st.warning(answer)
                        else:
                            st.success(answer)
                        
                        # 2. Agent Trace
                        st.markdown('<div class="card-header">🔍 Agent Workflow Execution Trace</div>', unsafe_allow_html=True)
                        if agent_trace:
                            for idx, step in enumerate(agent_trace):
                                step_num = idx + 1
                                agent_name = step.get("agent", "unknown").replace("_node", "").upper()
                                with st.expander(f"Step {step_num}: {agent_name} AGENT"):
                                    st.markdown("**Input Payload:**")
                                    st.code(step.get("input", ""), language="text")
                                    st.markdown("**Response Generated:**")
                                    st.code(step.get("output", ""), language="markdown")
                        else:
                            st.info("No trace items returned by the agent.")
                            
                        # 3. Raw Response
                        st.markdown('<div class="card-header">🛠️ Developer Diagnostics</div>', unsafe_allow_html=True)
                        with st.expander("Show Raw JSON API Response"):
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
