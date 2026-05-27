# Curl Examples for Testing self-hosted Qwen API

Use these commands to test the model server endpoint directly and the fully-integrated agent backend.

## 1. Direct Qwen API Tests (vLLM on Port 8001)

### Check Available Models
vLLM exposes standard OpenAI `/v1/models` endpoint to query active models.

```bash
curl -X GET http://localhost:8001/v1/models
```

### Chat Completion Test
Send a prompt to the model directly, including temperature, top_p, and max_tokens parameters:

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen14b",
    "messages": [
      {
        "role": "user",
        "content": "Briefly explain what vLLM is."
      }
    ],
    "temperature": 0.2,
    "top_p": 0.8,
    "repetition_penalty": 1.05,
    "max_tokens": 512
  }'
```

---

## 2. Integrated Agent Flow Test (FastAPI on Port 8000)

After starting both Qwen and the FastAPI backend, run this curl request to test the multi-agent manufacturing QA reasoning loop.

```bash
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "A batch of machined parts has an outer diameter deviation of +0.05mm. The machine is CNC-01, the material is 45 steel, and the cutting tool was recently replaced. Please analyze possible causes and provide troubleshooting steps.",
    "user_id": "demo_user",
    "context": {}
  }'
```
