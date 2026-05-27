import os
import sys
import time
import uuid
import torch
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

# Load env variables from parent directory if .env is there
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, ".env"))

app = FastAPI(title="Transformers Qwen Server", version="1.0.0")

# 1. Environment & Config checks
QWEN_MODEL_PATH = os.getenv("QWEN_MODEL_PATH", "/data/models/Qwen2.5-7B-Instruct")
QWEN_SERVED_MODEL_NAME = os.getenv("QWEN_SERVED_MODEL_NAME", "qwen7b")
QWEN_DEVICE = os.getenv("QWEN_DEVICE", "cuda")
QWEN_DTYPE = os.getenv("QWEN_DTYPE", "auto")

QWEN_MAX_NEW_TOKENS = int(os.getenv("QWEN_MAX_NEW_TOKENS", "2048"))
QWEN_TEMPERATURE = float(os.getenv("QWEN_TEMPERATURE", "0.2"))
QWEN_TOP_P = float(os.getenv("QWEN_TOP_P", "0.8"))
QWEN_REPETITION_PENALTY = float(os.getenv("QWEN_REPETITION_PENALTY", "1.05"))

# Verify model paths before loading
if not os.path.exists(QWEN_MODEL_PATH):
    print(f"Error: Model path '{QWEN_MODEL_PATH}' does not exist.")
    sys.exit(1)

config_path = os.path.join(QWEN_MODEL_PATH, "config.json")
if not os.path.exists(config_path):
    print(f"Error: config.json not found in model path '{QWEN_MODEL_PATH}'.")
    sys.exit(1)

# Set up torch dtype
dtype_map = {
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
    "float32": torch.float32,
}
torch_dtype = dtype_map.get(QWEN_DTYPE.lower(), "auto")

# 2. Load tokenizer and model
print(f"Loading Qwen model from: {QWEN_MODEL_PATH}")
print(f"Using device: {QWEN_DEVICE}, dtype: {QWEN_DTYPE}")

try:
    tokenizer = AutoTokenizer.from_pretrained(QWEN_MODEL_PATH, trust_remote_code=True)
    if QWEN_DEVICE == "auto":
        model = AutoModelForCausalLM.from_pretrained(
            QWEN_MODEL_PATH,
            torch_dtype=torch_dtype,
            device_map="auto",
            trust_remote_code=True
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            QWEN_MODEL_PATH,
            torch_dtype=torch_dtype,
            device_map={"": QWEN_DEVICE},
            trust_remote_code=True
        )
    print("Model loaded successfully!")
except Exception as e:
    print(f"Failed to load model: {e}")
    sys.exit(1)

# Pydantic Schemas
class ChatMessage(BaseModel):
    role: str
    content: str

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

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"

class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: ChatCompletionUsage

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/v1/models")
def get_models():
    return {
        "object": "list",
        "data": [
            {
                "id": QWEN_SERVED_MODEL_NAME,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "qwen"
            }
        ]
    }

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Streaming is not supported by this server."
        )

    # Use defaults if not specified in request
    temp = request.temperature if request.temperature is not None else QWEN_TEMPERATURE
    top_p_val = request.top_p if request.top_p is not None else QWEN_TOP_P
    max_toks = request.max_tokens if request.max_tokens is not None else QWEN_MAX_NEW_TOKENS
    rep_pen = request.repetition_penalty if request.repetition_penalty is not None else QWEN_REPETITION_PENALTY

    # Convert request messages to dictionaries
    msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        # Resolve prompt via chat template
        try:
            prompt = tokenizer.apply_chat_template(
                msg_dicts,
                tokenize=False,
                add_generation_prompt=True
            )
        except Exception as e:
            print(f"Warning: apply_chat_template failed ({e}), falling back to manual formatting.")
            prompt = ""
            for m in msg_dicts:
                role = m['role']
                content = m['content']
                prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
            prompt += "<|im_start|>assistant\n"

        # Tokenize prompt and send to device
        inputs = tokenizer([prompt], return_tensors="pt")
        device = getattr(model, "device", next(model.parameters()).device)
        input_ids = inputs.input_ids.to(device)
        attention_mask = inputs.attention_mask.to(device)

        # Build generation arguments
        do_sample = temp > 0
        gen_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "max_new_tokens": max_toks,
            "repetition_penalty": rep_pen,
            "do_sample": do_sample,
            "pad_token_id": tokenizer.eos_token_id
        }
        if do_sample:
            gen_kwargs["temperature"] = temp
            gen_kwargs["top_p"] = top_p_val

        # Execute model inference
        with torch.no_grad():
            outputs = model.generate(**gen_kwargs)

        # Decode newly generated tokens only
        prompt_len = input_ids.shape[1]
        response_ids = outputs[0][prompt_len:]
        response_text = tokenizer.decode(response_ids, skip_special_tokens=True)

        # Calculate token counts
        prompt_tokens = prompt_len
        completion_tokens = len(response_ids)
        total_tokens = prompt_tokens + completion_tokens

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=response_text)
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
