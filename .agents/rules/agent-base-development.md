---
trigger: always_on
---

# Project Rules for Agent Base Development

## Project Goal

This project is a modular AI agent base built with FastAPI, LangGraph, Dify-compatible HTTP APIs, and a React/Vite frontend.


MiniMax is the default model provider because the user has purchased a MiniMax Token Plan. However, the whole system must be provider-agnostic so that the user can later switch to other API providers or locally deployed models such as Qwen, vLLM, Ollama, LM Studio, or any OpenAI-compatible endpoint.

## Core Architecture Rules

1. Do not hard-code the application around MiniMax.
2. MiniMax must be implemented as one provider adapter, not as the center of the architecture.
3. All model calls must go through a common provider abstraction layer.
4. The LangGraph workflow must not directly call MiniMax APIs.
5. The frontend must not directly call MiniMax APIs.
6. The frontend must never receive API keys or secrets.
7. The backend must start successfully even if MiniMax API key is missing, local Qwen is not running, or another provider is unavailable.
8. Providers should be lazily initialized and fail gracefully.
9. Provider-specific request parameters should be isolated from the generic agent workflow.
10. Adding a new provider should not require rewriting the LangGraph workflow or frontend business logic.

## Required Provider Abstraction

Create and maintain a BaseModelProvider interface with methods such as:

* chat
* generate_image
* image_to_image
* generate_video
* text_to_speech
* speech_to_text if supported
* generate_music
* upload_file
* list_files
* download_file
* delete_file

Implement at least:

* MiniMaxProvider
* OpenAICompatibleProvider
* LocalQwenProvider or a local OpenAI-compatible provider wrapper

MiniMax is the default provider.

## MiniMax Rules

1. Use MiniMax as the default provider.
2. Read MiniMax configuration from environment variables:

   * MINIMAX_API_KEY
   * MINIMAX_BASE_URL
   * MINIMAX_DEFAULT_TEXT_MODEL
   * MINIMAX_DEFAULT_IMAGE_MODEL
   * MINIMAX_DEFAULT_VIDEO_MODEL
   * MINIMAX_DEFAULT_SPEECH_MODEL
   * MINIMAX_DEFAULT_MUSIC_MODEL
3. Do not expose MiniMax API keys to the frontend.
4. Keep MiniMax endpoint paths and model names configurable.
5. Implement robust error handling, timeout handling, retry logic, and structured logs.
6. For asynchronous tasks such as video or music generation, implement task creation, polling, result fetching, and media download.

## Dify Integration Rules

1. Expose clean HTTP endpoints that can be called by Dify HTTP Request nodes.
2. Use consistent JSON response format:
   {
   "success": true,
   "provider": "...",
   "task_type": "...",
   "data": {},
   "trace": [],
   "error": null
   }
3. Provide Dify request examples in documentation.
4. Dify should call the FastAPI backend, not MiniMax directly.

## LangGraph Rules

1. LangGraph is the agent orchestration layer.
2. LangGraph nodes should call provider abstraction methods, not vendor-specific APIs.
3. The workflow should support:

   * task classification
   * provider selection
   * tool calling
   * file operations
   * multimodal generation
   * structured trace output
4. Return useful traces for frontend debugging.

## Frontend Rules

The frontend should include tabs or pages for:

* Chat
* Image generation
* Image-to-image generation
* Video generation
* Speech
* Music
* MiniMax file management
* Local file agent
* Settings

The Settings page should allow provider selection:

* minimax
* openai_compatible
* local_qwen

The frontend must show:

* request status
* task trace
* generated media preview
* download links
* raw JSON response toggle
* readable error messages

## Local File Agent Safety Rules

The local file agent is allowed to modify files only under the configured FILE_WORKSPACE_ROOT.

Strict requirements:

1. Prevent path traversal.
2. Resolve and validate all paths before reading or writing.
3. Default to dry-run mode.
4. Show a modification plan before applying changes.
5. Show unified diffs for text edits.
6. Create timestamped backups before overwriting or deleting files.
7. Store backups under .agent_backups.
8. Refuse to edit binary files unless explicitly supported.
9. Refuse to edit files larger than the configured size limit.
10. Log every file operation.
11. Do not implement unrestricted shell execution unless explicitly requested later.
12. Never read or modify files outside FILE_WORKSPACE_ROOT.

## Development Quality Rules

1. Use Python 3.11+.
2. Use FastAPI and Pydantic for typed APIs.
3. Use TypeScript on the frontend.
4. Keep modules small and maintainable.
5. Add .env.example.
6. Add README.md.
7. Add docs/architecture.md.
8. Add docs/provider_adapter_guide.md.
9. Add docs/file_safety.md.
10. Add minimal tests for provider abstraction and safe file editing.
11. Do not introduce unnecessary dependencies.
12. Do not commit secrets or API keys.
13. When uncertain about an external API parameter, create a clearly marked TODO and avoid inventing fake parameters.
14. Prefer clean, extensible architecture over quick hard-coded demos.