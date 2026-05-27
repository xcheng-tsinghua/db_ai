# Streamlit Test Web UI

This directory contains a simple, premium-designed Streamlit application for testing and debugging the Dify + LangGraph + Qwen MVP reasoning chain.

---

## 1. Installation

Install the required dependencies:
```bash
pip install -r web_ui/requirements_web.txt
```

---

## 2. Launch Sequence

To test the entire system, start the services in the following order:

### Step 1: Start Qwen Model Server
Run the local direct Transformers server:
```bash
bash qwen_server_transformers/start_qwen_transformers.sh
```

### Step 2: Start FastAPI LangGraph Backend
Start the main application server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step 3: Start Streamlit Web UI
Run the Streamlit frontend:
```bash
bash web_ui/start_web_ui.sh
```
The server will run on `0.0.0.0:8501` by default.

---

## 3. Remote Access from Laptop

To open the testing UI on your laptop:

### Option A: Direct Access (Firewall open)
If port `8501` is open in your server's security group/firewall, open your laptop browser and navigate to:
```
http://<SERVER_IP>:8501
```

### Option B: SSH Port Forwarding (Recommended / Safe)
If port `8501` is blocked or you want to keep the UI private:
1. Open a terminal on your laptop and run:
   ```bash
   ssh -L 8501:127.0.0.1:8501 user@<SERVER_IP>
   ```
2. Open your laptop browser and navigate to:
   ```
   http://127.0.0.1:8501
   ```
All traffic to port `8501` on your laptop will be securely tunneled over SSH to the server.

---

## 4. Model Provider Selection & Examples

The Web UI features a sidebar panel called **"Model Provider Override"** allowing you to dynamically route queries through either the local model or custom external APIs.

### Option 1: Local Qwen
This is the default local option. No API key is required.
* **Base URL**: `http://127.0.0.1:8001/v1`
* **Model Name**: `qwen7b`

### Option 2: MiniMax API (Default External Provider)
This is the default option for external API calls.
* **Base URL**: `https://api.minimax.chat/v1`
* **Model Name**: `MiniMax-M1`
* **API Key**: Enter your MiniMax API key in the password field.

### Option 3: Custom OpenAI-compatible API
Use this for other external providers:
1. **OpenAI API**:
   * **API Base URL**: `https://api.openai.com/v1`
   * **Model Name**: `gpt-4o-mini`
   * **API Key**: `sk-...` (Input is protected via password text field)
2. **DeepSeek API**:
   * **API Base URL**: `https://api.deepseek.com/v1`
   * **Model Name**: `deepseek-chat`
   * **API Key**: `sk-...`
3. **DashScope/Qwen API**:
   * **API Base URL**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
   * **Model Name**: `qwen-plus`
   * **API Key**: `sk-...`

Click **"Test Selected Model Connection"** in the sidebar to verify your configurations.

---

## 5. Security & Key Handling Guidelines

> [!WARNING]
> - **In-Memory Lifespan Only**: All custom API credentials inputted into the Web UI are sent as transient request-level context to the backend. They exist solely in-memory on the backend for the duration of that specific API transaction and are never logged, cached, or written to disk.
> - **PoC/Local Environment Only**: This UI has no native authentication. Do not expose port 8501 publicly to the web.
> - **Production Note**: For production systems, credentials should be retrieved from a secure server-side encrypted vault rather than entered directly via client-side browsers.
