# System Architecture Overview

This project is a modular AI agent base built around FastAPI, LangGraph, and a React + Vite + TypeScript frontend. It is designed to be model provider-agnostic, enabling unified routing across text, image, video, speech, and music generation tasks, alongside a safe local file agent.

## Structural Components

The application is structured into the following layers:

```
[ Frontend: React / TS / CSS ] (Vite server on :5173)
             │
             ▼
[ Backend API: FastAPI ] (Uvicorn server on :8001)
             │
             ├───────────────► [ Settings & Dynamic Registry Router ]
             │
             ├───────────────► [ Direct Multimodal Endpoints ]
             │
             └───────────────► [ LangGraph Orchestration Workflow ]
                                         │
                                         ├─► Node 1: Task Classification
                                         │
                                         ├─► Node 2: OpenAI Compatible Chat Completion
                                         │
                                         ├─► Node 3: Multimodal Generation
                                         │
                                         └─► Node 4: Safe Local File Agent Tool
                                                     (Unified Diff & Backups)
```

### 1. Model Provider Abstraction
All AI capabilities are declared under the `BaseModelProvider` interface:
*   `chat`: Chat completion responses
*   `generate_image` / `image_to_image`: Image synthesis
*   `generate_video` / `generate_music`: Async task-based media generation
*   `text_to_speech` / `speech_to_text`: Speech synthesis and transcribing
*   `upload_file` / `list_files` / `download_file` / `delete_file`: Files DB operations

Individual provider classes (e.g. `MiniMaxProvider`, `OpenAICompatibleProvider`, `LocalQwenProvider`) inherit from this interface, wrapping vendor-specific REST APIs. The `ProviderManager` dynamically routes workflow requests to the active adapter and supports dynamically switching providers.

### 2. LangGraph Workflow Routing
The agent uses a LangGraph `StateGraph` to manage tasks:
1.  **Task Classification & Routing Node:** Evaluates user prompt segments to determine if it is standard text, media generation, or file edits. If keys are missing, it falls back to a rule-based parser.
2.  **Execution Nodes:** Dynamically invokes appropriate provider adapters or runs the Local File Agent.
3.  **Trace Accumulator:** Aggreates node results and trace records, returning them as structured outputs to the frontend.

### 3. Local File Safety Agent
The file agent protects files under `FILE_WORKSPACE_ROOT` from unintended damage:
*   Blocks path traversals.
*   Enforces dry-runs, allowing user preview of file plans.
*   Shows unified color-coded diff displays of changes.
*   Saves backups under `.agent_backups/` before modifying files.
