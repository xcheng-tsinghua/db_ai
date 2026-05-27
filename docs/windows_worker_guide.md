# Windows Agent Worker Component Guide

The Windows Agent Worker is a lightweight, secure helper service designed to run locally on your Windows host. It bridges the FastAPI server backend with local operating system capabilities, executing safe local tasks under a restricted sandbox model.

---

## 1. Purpose & Design Architecture

Unlike the server-side backend (which coordinates the core LangGraph reasoning workflow and calls LLMs), the Windows Worker runs directly on your local workstation. It receives instructions from the backend to interact with your local environment:

```
+------------------+     /agent/invoke     +-------------------+
|  Streamlit UI   | ---------------------> | FastAPI Backend   |
| (Laptop Browser) |                       | (LangGraph Node)  |
+------------------+                       +-------------------+
        ^                                            |
        | (Worker proxy API)                         | (HTTP Client)
        +--------------------------------------------v
                                           +-------------------+
                                           | Windows Worker    | (Port 9100)
                                           | (FastAPI Sandbox) |
                                           +-------------------+
                                                     |
                                                     v
                                           +-------------------+
                                           | Local Host OS     | (Screenshot, Files,
                                           | & Workspace Dir   |  Browser, Python)
                                           +-------------------+
```

---

## 2. Security Configuration & Sandboxing

The worker restricts actions to protect host integrity:
- **Sandbox Directory (`WINDOWS_WORKSPACE_DIR`)**: All file operations (`list_dir`, `read_text_file`, `write_text_file`), Python scripts, and screenshot saves are strictly confined to this folder (e.g. `C:\ai_worker_workspace`). Path traversal (e.g. `..\`) and absolute path execution outside of the workspace are strictly prohibited.
- **Explicit Feature Flags**:
  - `ALLOW_SHELL`: Off (`false`) by default. Enabling this allows arbitrary PowerShell commands, which is powerful but risky.
  - `ALLOW_FILE_WRITE`: Controls file modification within the workspace.
  - `ALLOW_SCREENSHOT`: Allows grabbing the primary screen contents.
  - `ALLOW_BROWSER_OPEN`: Allows opening verified `http://` / `https://` links.

---

## 3. Installation Instructions

Follow these steps to set up the worker on your Windows laptop:

1. **Open PowerShell** as a standard user.
2. **Navigate to the Repository Root**:
   ```powershell
   cd e:\document\DeepLearning\db_ai
   ```
3. **Initialize Virtual Environment** (Optional but recommended):
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. **Install Windows Worker Dependencies**:
   ```powershell
   pip install -r windows_worker\requirements_windows.txt
   ```

---

## 4. Setup Workspace Sandbox

1. **Create the Workspace Directory**:
   By default, the workspace directory is `C:\ai_worker_workspace`. Create it manually via File Explorer or PowerShell:
   ```powershell
   New-Item -ItemType Directory -Path "C:\ai_worker_workspace" -Force
   ```

---

## 5. Configure `.env.windows`

1. The startup script automatically copies `windows_worker\.env.windows.example` to `windows_worker\.env.windows` on the first launch.
2. Open `windows_worker\.env.windows` and check/edit settings:
   ```ini
   WINDOWS_WORKER_HOST=127.0.0.1
   WINDOWS_WORKER_PORT=9100
   WINDOWS_WORKSPACE_DIR=C:\ai_worker_workspace
   ALLOW_SHELL=false
   ALLOW_FILE_WRITE=true
   ALLOW_SCREENSHOT=true
   ALLOW_BROWSER_OPEN=true
   ```

---

## 6. Starting the Worker

Execute using PowerShell or standard Command Prompt:
* **Using PowerShell**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File windows_worker\start_worker.ps1
  ```
* **Using Batch File**:
  ```cmd
  windows_worker\start_worker.bat
  ```

---

## 7. Verification and Testing

### Test Connection Locally
You can verify the worker is listening locally by making a simple request from PowerShell:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9100/health" -Method Get
```
Or using `curl` from CMD:
```bash
curl http://127.0.0.1:9100/health
```

Expected Response:
```json
{
  "status": "healthy",
  "workspace_dir": "C:\\ai_worker_workspace",
  "allow_shell": false,
  "allow_file_write": true,
  "allow_screenshot": true,
  "allow_browser_open": true
}
```

---

## 8. Connecting the FastAPI Backend Server

To configure the central FastAPI backend to communicate with this worker:

1. Open the backend's `.env` configuration file in the project root.
2. Add/enable the following keys:
   ```ini
   ENABLE_WINDOWS_WORKER=true
   WINDOWS_WORKER_BASE_URL=http://127.0.0.1:9100
   ```
3. Restart the FastAPI backend server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

Now, the Streamlit UI can connect to the proxy endpoints, allowing you to test the worker tools!
