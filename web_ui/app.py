import os
import requests
import datetime
import base64
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

# Sidebar Configuration
st.sidebar.markdown("### ⚙️ Connection Settings")
default_backend_url = os.getenv("AGENT_API_URL", "http://127.0.0.1:8000/agent/invoke")
backend_url = st.sidebar.text_input("FastAPI Endpoint URL", value=default_backend_url)

# Model Provider Override Configs
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Model Provider Override")

llm_provider = st.sidebar.radio(
    "Select Provider",
    options=["Local Qwen", "MiniMax API"],
    index=0
)

if llm_provider == "Local Qwen":
    llm_base_url = "http://127.0.0.1:8001/v1"
    llm_model = "qwen7b"
    llm_api_key = "EMPTY"
    
    # Render selections statically
    st.sidebar.markdown("**Provider**: `Local Qwen`")
    st.sidebar.markdown(f"**Base URL**: `{llm_base_url}`")
    st.sidebar.markdown(f"**Model**: `{llm_model}`")
    st.sidebar.markdown("**API Key**: `[EMPTY]` (Disabled)")
    
    temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.5, value=0.2, step=0.1)
    max_tokens = st.sidebar.number_input("Max Output Tokens", min_value=1, max_value=8192, value=2048)
elif llm_provider == "MiniMax API":
    st.sidebar.warning(
        "⚠️ MiniMax API credentials are sent in-memory for this request only. "
        "Do not expose this Web UI publicly without authentication."
    )
    llm_base_url = st.sidebar.text_input("API Base URL Override", value="https://api.minimax.io/v1")
    llm_model = st.sidebar.text_input("Model Name Override", value="MiniMax-M2.7-highspeed")
    default_key = os.getenv("MINIMAX_API_KEY", "")
    llm_api_key = st.sidebar.text_input("API Key (Password Field)", type="password", value=default_key, placeholder="Paste MiniMax API key here")
    temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.5, value=0.2, step=0.1)
    max_tokens = st.sidebar.number_input("Max Output Tokens", min_value=1, max_value=8192, value=2048)
    
    masked_key = llm_api_key[:4] + "..." if len(llm_api_key) > 4 else "..." if llm_api_key else "None"
    st.sidebar.markdown("**Provider**: `MiniMax API`")
    st.sidebar.markdown(f"**Base URL**: `{llm_base_url}`")
    st.sidebar.markdown(f"**Model**: `{llm_model}`")
    st.sidebar.markdown(f"**API Key**: `{masked_key}`")

llm_supports_vision = False
if llm_provider == "Local Qwen":
    llm_supports_vision = "vl" in llm_model.lower()
    llm_supports_vision = st.sidebar.checkbox(
        "Local model supports image understanding",
        value=llm_supports_vision,
        help="Enable only when your local endpoint serves a Qwen-VL or other vision-capable model."
    )
elif llm_provider == "MiniMax API":
    llm_supports_vision = any(
        marker in llm_model.lower()
        for marker in ("vl", "vision", "multimodal", "minimax-01")
    )
    llm_supports_vision = st.sidebar.checkbox(
        "MiniMax model supports image understanding",
        value=llm_supports_vision,
        help="Enable if the selected MiniMax model (e.g. MiniMax-VL-01) supports image understanding."
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### Image Output")
enable_image_output = False
image_output_mode = "auto"
image_generation_model = "image-01"
output_image_aspect_ratio = "1:1"
output_image_count = 1

minimax_api_key_env = os.getenv("MINIMAX_API_KEY", "")
show_image_output = (llm_provider == "MiniMax API") or bool(minimax_api_key_env)

if show_image_output:
    enable_image_output = st.sidebar.checkbox(
        "Enable MiniMax image output",
        value=False,
        help="Uses MiniMax /v1/image_generation when your prompt requests an image."
    )
    if enable_image_output:
        image_output_mode = st.sidebar.selectbox(
            "Image Output Mode",
            options=["auto", "always"],
            index=0,
            help="Auto generates images only for image-generation prompts. Always generates for every request."
        )
        image_generation_model = st.sidebar.text_input("Image Model", value="image-01")
        output_image_aspect_ratio = st.sidebar.selectbox(
            "Aspect Ratio",
            options=["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"],
            index=0
        )
        output_image_count = st.sidebar.number_input("Image Count", min_value=1, max_value=9, value=1)


# Test Selected Model Button
if st.sidebar.button("🔌 Test Selected Model Connection", use_container_width=True):
    if llm_provider in ["MiniMax API", "Custom OpenAI-compatible API"] and not llm_api_key:
        st.sidebar.error("Error: Please enter an API key for the selected provider.")
    else:
        with st.sidebar.spinner("Testing model connection..."):
            test_url = backend_url.replace("/agent/invoke", "/llm/test")
            provider_key = "local_qwen" if llm_provider == "Local Qwen" else "minimax" if llm_provider == "MiniMax API" else "custom_openai"
            test_payload = {
                "llm_provider": provider_key,
                "llm_base_url": llm_base_url,
                "llm_model": llm_model,
                "llm_api_key": llm_api_key if llm_api_key else "EMPTY"
            }
            try:
                test_res = requests.post(test_url, json=test_payload, timeout=10)
                if test_res.status_code == 200:
                    res_json = test_res.json()
                    if res_json.get("success"):
                        st.sidebar.success("Connection Successful!")
                    else:
                        err_text = res_json.get("error", "Unknown error")
                        st.sidebar.error(f"Failed: {err_text}")
                        if provider_key == "local_qwen":
                            st.sidebar.warning("⚠️ Local Qwen is not running. You can still choose MiniMax or another API.")
                else:
                    st.sidebar.error(f"Failed (Status {test_res.status_code}): {test_res.text}")
                    if provider_key == "local_qwen":
                        st.sidebar.warning("⚠️ Local Qwen is not running. You can still choose MiniMax or another API.")
            except Exception as e:
                st.sidebar.error(f"Connection Error: {e}")
                if provider_key == "local_qwen":
                    st.sidebar.warning("⚠️ Local Qwen is not running. You can still choose MiniMax or another API.")

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
        if "model_configured" in data:
            st.sidebar.markdown(f"**Served LLM**: `{data.get('model_configured', 'unknown')}`")
            st.sidebar.markdown(f"**API Base URL**: `{data.get('base_url', 'unknown')}`")
    else:
        st.sidebar.markdown(f"**Backend Health**: ⚠️ `STATUS {health_response.status_code}`")
except Exception:
    st.sidebar.markdown("**Backend Health**: ❌ `OFFLINE`")

# Windows Worker Test Section
st.sidebar.markdown("---")
with st.sidebar.expander("🖥️ Windows Worker Test", expanded=False):
    worker_health_url = backend_url.replace("/agent/invoke", "/worker/health")
    worker_list_url = backend_url.replace("/agent/invoke", "/worker/tools/list")
    worker_execute_url = backend_url.replace("/agent/invoke", "/worker/tools/execute")
    
    # 1. Health Status
    col_h1, col_h2 = st.columns([1, 1])
    with col_h1:
        st.markdown("**Status**")
    with col_h2:
        try:
            h_res = requests.get(worker_health_url, timeout=3)
            if h_res.status_code == 200:
                h_data = h_res.json()
                st.markdown("<span style='color:#10b981; font-weight:bold;'>ONLINE</span>", unsafe_allow_html=True)
                allow_shell = h_data.get("allow_shell", False)
            else:
                st.markdown("<span style='color:#ef4444; font-weight:bold;'>OFFLINE</span>", unsafe_allow_html=True)
                allow_shell = False
        except Exception:
            st.markdown("<span style='color:#ef4444; font-weight:bold;'>OFFLINE</span>", unsafe_allow_html=True)
            allow_shell = False
            
    # 2. List tools
    if st.button("📋 List Available Tools", use_container_width=True):
        try:
            l_res = requests.post(worker_list_url, timeout=5)
            if l_res.status_code == 200:
                tools_list = l_res.json()
                if not tools_list:
                    st.info("No tools registered.")
                for t in tools_list:
                    st.markdown(f"**`{t.get('name')}`**")
                    st.markdown(f"<span style='font-size:0.9rem; color:#cbd5e1;'>{t.get('description')}</span>", unsafe_allow_html=True)
            else:
                st.error(f"Error listing tools: {l_res.text}")
        except Exception as e:
            st.error(f"Error: {e}")
            
    # 3. Tool Execution Forms
    st.markdown("**Execute Tool**")
    tool_options = ["list_dir", "read_text_file", "write_text_file", "open_url", "take_screenshot"]
    if allow_shell:
        tool_options.append("run_powershell_command")
        
    selected_tool = st.selectbox(
        "Select Tool",
        options=tool_options,
        key="selected_worker_tool"
    )
    
    with st.form("worker_tool_form"):
        args = {}
        if selected_tool == "list_dir":
            rel_path = st.text_input("Relative Path", value=".", key="list_dir_rel_path")
            args = {"relative_path": rel_path}
        elif selected_tool == "read_text_file":
            rel_path = st.text_input("Relative Path", value="notes/test.txt", key="read_text_rel_path")
            args = {"relative_path": rel_path}
        elif selected_tool == "write_text_file":
            rel_path = st.text_input("Relative Path", value="notes/test.txt", key="write_text_rel_path")
            file_content = st.text_area("File Content", value="Hello from AI worker", key="write_text_content")
            args = {"relative_path": rel_path, "content": file_content}
        elif selected_tool == "open_url":
            url_to_open = st.text_input("URL", value="https://api.minimax.chat/", key="open_url_val")
            args = {"url": url_to_open}
        elif selected_tool == "take_screenshot":
            screenshot_path = st.text_input("Relative Path", value="screenshot.png", key="take_screenshot_rel_path")
            args = {"relative_path": screenshot_path}
        elif selected_tool == "run_powershell_command":
            cmd_to_run = st.text_input("PowerShell Command", value="Get-Process", key="run_ps_cmd")
            args = {"command": cmd_to_run}
            
        run_tool_btn = st.form_submit_button("▶️ Run Tool", use_container_width=True)
        
    if run_tool_btn:
        with st.spinner(f"Running {selected_tool}..."):
            try:
                exec_payload = {
                    "tool_name": selected_tool,
                    "arguments": args,
                    "request_id": f"ui-{int(datetime.datetime.now().timestamp())}"
                }
                exec_res = requests.post(worker_execute_url, json=exec_payload, timeout=65)
                if exec_res.status_code == 200:
                    res_json = exec_res.json()
                    if res_json.get("success"):
                        st.success("Tool execution successful!")
                        result_data = res_json.get("result")
                        st.json(result_data)
                        
                        # Render inline screenshot if output contains base64 image data
                        if isinstance(result_data, dict) and "image_base64" in result_data:
                            try:
                                import base64
                                st.image(
                                    base64.b64decode(result_data["image_base64"]),
                                    caption=f"Captured Screenshot ({result_data.get('width')}x{result_data.get('height')})",
                                    use_container_width=True
                                )
                            except Exception as img_err:
                                st.error(f"Failed to render screenshot image: {img_err}")
                    else:
                        st.error(f"Execution failed: {res_json.get('error')}")
                else:
                    st.error(f"Proxy error ({exec_res.status_code}): {exec_res.text}")
            except Exception as e:
                st.error(f"Failed calling worker: {e}")

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
        
        # File Uploader for Multimodal Input Image
        uploaded_file = st.file_uploader(
            "Upload Input Image (Optional for Vision analysis)",
            type=["png", "jpg", "jpeg", "webp"],
            key="vision_input_image"
        )
        
        image_base64 = None
        image_mime_type = None
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            image_base64 = base64.b64encode(bytes_data).decode("utf-8")
            image_mime_type = uploaded_file.type
            st.image(uploaded_file, caption="Input Image Preview", width=300)
            if llm_provider == "MiniMax API":
                st.info(
                    "MiniMax chat will not inspect this image directly. If image output is enabled, "
                    "the image can be sent to MiniMax image generation as a reference."
                )
            elif not llm_supports_vision:
                st.warning(
                    "The selected local model is marked as text-only. The backend will keep the request valid, "
                    "but the model will not inspect the image content."
                )
            
        user_id = st.text_input("User ID", value="web_demo_user")
        
        submit_btn = st.form_submit_button("🚀 Invoke Agent Workflow", use_container_width=True)

# Process form submission
if submit_btn:
    if not query.strip():
        with col_output:
            st.warning("Please enter a query prompt before submitting.")
    elif llm_provider in ["MiniMax API"] and not llm_api_key:
        with col_output:
            st.error("Error: Please enter an API key in the sidebar configuration to call the external LLM provider.")
    else:
        with col_output:
            # Spinner loader
            with st.spinner("Invoking LangGraph Workflow... Calling local/custom LLM..."):
                context_payload = {
                    "llm_provider": "local_qwen" if llm_provider == "Local Qwen" else "minimax",
                    "llm_base_url": llm_base_url,
                    "llm_model": llm_model,
                    "llm_api_key": llm_api_key,
                    "llm_temperature": temperature,
                    "llm_max_tokens": max_tokens,
                    "llm_supports_vision": llm_supports_vision,
                    "enable_image_output": enable_image_output,
                    "image_output_mode": image_output_mode,
                    "image_generation_model": image_generation_model,
                    "output_image_aspect_ratio": output_image_aspect_ratio,
                    "output_image_count": output_image_count
                }
                if image_base64:
                    context_payload["image_base64"] = image_base64
                    context_payload["image_mime_type"] = image_mime_type
                    
                payload = {
                    "query": query,
                    "user_id": user_id,
                    "context": context_payload
                }
                
                try:
                    response = requests.post(backend_url, json=payload, timeout=300)
                    
                    if response.status_code == 200:
                        res_data = response.json()
                        error_msg = res_data.get("error")
                        answer = res_data.get("answer", "")
                        task_type = res_data.get("task_type", "unknown")
                        need_review = res_data.get("need_human_review", False)
                        agent_trace = res_data.get("agent_trace", [])
                        warnings = res_data.get("warnings", [])
                        output_images = res_data.get("output_images", [])
                        
                        # Style Badge Header Container
                        badge_html = f'<span class="badge badge-task-type">Task: {task_type.upper()}</span>'
                        if need_review:
                            badge_html += '<span class="badge badge-review-needed">⚠️ HUMAN REVIEW REQUIRED</span>'
                        else:
                            badge_html += '<span class="badge badge-review-ok">✅ STABLE: NO REVIEW NEEDED</span>'
                        
                        st.markdown(f"<div>{badge_html}</div><br>", unsafe_allow_html=True)
                        
                        # 1. Final Answer Card
                        st.markdown('<div class="card-header">📊 Final Diagnostic Report</div>', unsafe_allow_html=True)
                        
                        # Use success/warning/error alert panels for contrast rendering
                        if error_msg:
                            st.error(error_msg)
                        elif need_review:
                            st.warning(answer)
                        else:
                            st.success(answer)

                        if warnings:
                            for warning_msg in warnings:
                                st.warning(warning_msg)

                        if output_images:
                            st.markdown('<div class="card-header">Generated Images</div>', unsafe_allow_html=True)
                            for image_idx, image_item in enumerate(output_images, start=1):
                                caption = f"Generated Image {image_idx}"
                                provider = image_item.get("provider")
                                model = image_item.get("model")
                                if provider or model:
                                    caption += f" ({provider or 'provider unknown'} / {model or 'model unknown'})"

                                if image_item.get("image_base64"):
                                    try:
                                        st.image(
                                            base64.b64decode(image_item["image_base64"]),
                                            caption=caption,
                                            use_container_width=True
                                        )
                                    except Exception as img_err:
                                        st.error(f"Failed to render generated image: {img_err}")
                                elif image_item.get("url"):
                                    st.image(image_item["url"], caption=caption, use_container_width=True)
                                    st.markdown(f"[Open image URL]({image_item['url']})")
                        
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
                            
                    elif response.status_code == 400:
                        try:
                            err_data = response.json()
                            st.error(err_data.get("error", "Bad Request"))
                        except Exception:
                            st.error(f"Backend API Error (Status 400): {response.text}")
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
