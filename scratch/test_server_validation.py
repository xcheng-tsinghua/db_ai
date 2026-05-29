import os
import sys
import unittest
import threading
import time
import requests
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

# Set environment variable to bypass model loading in server.py
os.environ["QWEN_MODEL_PATH"] = "dummy"

# We will create a clean test app containing exactly the schemas and endpoint from server.py
app = FastAPI()

class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    repetition_penalty: Optional[float] = None
    stream: Optional[bool] = False

    class Config:
        extra = "allow"

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("\n--- VALIDATION ERROR DETECTED ---")
    print(exc.errors())
    print("---------------------------------\n")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    return {"status": "ok"}

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")

if __name__ == "__main__":
    # Start server in thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1) # wait for server to start

    # Test payload mimicking what the main app sends when an image is uploaded
    payload = {
        "model": "qwen7b",
        "messages": [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": [
                {"type": "text", "text": "What is in this image?"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}}
            ]}
        ],
        "temperature": 0.2,
        "max_tokens": 2048
    }

    print("Sending request with image...")
    res = requests.post("http://127.0.0.1:8002/v1/chat/completions", json=payload)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.json()}")

    # Now let's try other possible payloads that might be sent by openai client library
    # E.g. stop parameters, extra keys, etc.
    payload_extra = dict(payload)
    payload_extra["stop"] = ["<|im_end|>"]
    payload_extra["presence_penalty"] = 0.0
    print("\nSending request with extra parameters...")
    res_extra = requests.post("http://127.0.0.1:8002/v1/chat/completions", json=payload_extra)
    print(f"Status Code: {res_extra.status_code}")

    # Now let's test if there is a content=None message (e.g. tool calls)
    payload_none = {
        "model": "qwen7b",
        "messages": [
            {"role": "system", "content": "System prompt"},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "take_screenshot", "arguments": "{}"}}]}
        ]
    }
    print("\nSending request with assistant message content=None...")
    res_none = requests.post("http://127.0.0.1:8002/v1/chat/completions", json=payload_none)
    print(f"Status Code: {res_none.status_code}")
    print(f"Response: {res_none.json()}")
