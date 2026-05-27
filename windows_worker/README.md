# Windows Agent Worker Component

This component runs a lightweight, secure FastAPI service directly on your Windows host. It exposes local tools (file actions, shell actions, browser launching, and screenshots) to the FastAPI server backend within a sandboxed environment.

---

## 🔒 Security Sandboxing

To protect host integrity, the Windows Agent Worker implements the following safety measures:
1. **Directory Confinement (`WINDOWS_WORKSPACE_DIR`)**: All directory listing, file reading, file writing, Python execution, and screenshot storage are strictly confined to this directory (e.g. `C:\ai_worker_workspace`). Path traversal using `..` or absolute drive paths targeting files outside the sandbox will return errors.
2. **Feature Control Flags**: 
   - `ALLOW_SHELL`: Disabled by default (`false`). When disabled, any request to execute PowerShell commands fails immediately.
   - `ALLOW_FILE_WRITE`: Controls file-creation capability.
   - `ALLOW_SCREENSHOT`: Controls whether the agent can capture screenshots of your primary monitor.
   - `ALLOW_BROWSER_OPEN`: Controls whether the agent can open HTTP/HTTPS URLs.

---

## 🚀 Setup & Launch Instructions

### 1. Install Dependencies
Run a Python environment setup inside this folder (or globally on the Windows host):
```bash
# Create and activate a virtual environment (optional)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r windows_worker\requirements_windows.txt
```

### 2. Configure environment
Rename/copy `.env.windows.example` to `.env.windows` and set your preferred workspace path:
```ini
WINDOWS_WORKER_HOST=127.0.0.1
WINDOWS_WORKER_PORT=9100
WINDOWS_WORKSPACE_DIR=C:\ai_worker_workspace
ALLOW_SHELL=false
ALLOW_FILE_WRITE=true
ALLOW_SCREENSHOT=true
ALLOW_BROWSER_OPEN=true
```

Create the directory configured (e.g., `C:\ai_worker_workspace` if using the default value).

### 3. Start the Worker Service
Run using either the batch file or PowerShell script:
* **Option A: PowerShell**
  ```powershell
  powershell -ExecutionPolicy Bypass -File windows_worker\start_worker.ps1
  ```
* **Option B: Batch Command**
  ```cmd
  windows_worker\start_worker.bat
  ```

---

## 🛠️ API & Tooling Endpoint
Once running, the worker exposes the following HTTP endpoints:
- `GET /health`: Check service status and safety configuration flags.
- `POST /tools/list`: Retrieve the metadata schema of all registered tools.
- `POST /tools/execute`: Execute a safe local tool.

### Request Body Format Example (`POST /tools/execute`):
```json
{
  "tool_name": "write_text_file",
  "arguments": {
    "relative_path": "notes/test.txt",
    "content": "Hello from AI worker!"
  },
  "request_id": "demo-001"
}
```
