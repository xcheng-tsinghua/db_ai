import os
import sys
import time
import uuid
import base64
import io
import torch
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
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
QWEN_ENABLE_VISION = os.getenv("QWEN_ENABLE_VISION", "auto").lower()

QWEN_MAX_NEW_TOKENS = int(os.getenv("QWEN_MAX_NEW_TOKENS", "2048"))
QWEN_TEMPERATURE = float(os.getenv("QWEN_TEMPERATURE", "0.2"))
QWEN_TOP_P = float(os.getenv("QWEN_TOP_P", "0.8"))
QWEN_REPETITION_PENALTY = float(os.getenv("QWEN_REPETITION_PENALTY", "1.05"))
VISION_MODEL_HINT = "vl" in f"{QWEN_MODEL_PATH} {QWEN_SERVED_MODEL_NAME}".lower()
USE_VISION = QWEN_ENABLE_VISION in {"1", "true", "yes"} or (
    QWEN_ENABLE_VISION == "auto" and VISION_MODEL_HINT
)

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
print(f"Vision mode: {'enabled' if USE_VISION else 'disabled'}")

try:
    processor = None
    if USE_VISION:
        try:
            from transformers import AutoProcessor
            try:
                from transformers import AutoModelForImageTextToText as VisionModelClass
            except ImportError:
                from transformers import Qwen2_5_VLForConditionalGeneration as VisionModelClass
        except Exception as import_error:
            raise RuntimeError(
                "Vision mode requires a Transformers version with Qwen-VL support. "
                "Install a recent transformers build and qwen-vl-utils."
            ) from import_error

        processor = AutoProcessor.from_pretrained(QWEN_MODEL_PATH, trust_remote_code=True)
        tokenizer = getattr(processor, "tokenizer", None) or AutoTokenizer.from_pretrained(
            QWEN_MODEL_PATH,
            trust_remote_code=True
        )
        if QWEN_DEVICE == "auto":
            model = VisionModelClass.from_pretrained(
                QWEN_MODEL_PATH,
                torch_dtype=torch_dtype,
                device_map="auto",
                trust_remote_code=True
            )
        else:
            model = VisionModelClass.from_pretrained(
                QWEN_MODEL_PATH,
                torch_dtype=torch_dtype,
                device_map={"": QWEN_DEVICE},
                trust_remote_code=True
            )
    else:
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
    return {
        "status": "healthy",
        "served_model": QWEN_SERVED_MODEL_NAME,
        "vision_enabled": USE_VISION
    }

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

def _content_to_text(content: Union[str, List[Dict[str, Any]]]) -> str:
    if isinstance(content, str):
        return content

    text_parts: list[str] = []
    image_count = 0
    for part in content:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "text":
            text_parts.append(str(part.get("text", "")))
        elif part.get("type") in {"image", "image_url", "input_image"}:
            image_count += 1

    if image_count:
        text_parts.append(
            f"[{image_count} image(s) were included in the request, but this local "
            "Qwen server is running in text-only mode. Start a Qwen-VL model and set "
            "QWEN_ENABLE_VISION=true to analyze image content.]"
        )
    return "\n\n".join(part for part in text_parts if part)

def _decode_data_url(data_url: str):
    try:
        from PIL import Image
    except ImportError as import_error:
        raise HTTPException(status_code=500, detail="Pillow is required for base64 image inputs.") from import_error

    if not data_url.startswith("data:"):
        return data_url
    try:
        _, encoded = data_url.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as decode_error:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image payload: {decode_error}") from decode_error

def _to_qwen_vl_messages(messages: List[ChatMessage]) -> list[dict[str, Any]]:
    converted_messages: list[dict[str, Any]] = []
    for message in messages:
        if isinstance(message.content, str):
            converted_messages.append({"role": message.role, "content": message.content})
            continue

        blocks: list[dict[str, Any]] = []
        for part in message.content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text":
                blocks.append({"type": "text", "text": str(part.get("text", ""))})
            elif part.get("type") in {"image_url", "input_image"}:
                image_field = part.get("image_url")
                if isinstance(image_field, dict):
                    image_url = image_field.get("url")
                else:
                    image_url = image_field or part.get("url")
                if image_url:
                    blocks.append({"type": "image", "image": _decode_data_url(image_url)})
            elif part.get("type") == "image":
                image_value = part.get("image") or part.get("url")
                if image_value:
                    blocks.append({"type": "image", "image": _decode_data_url(image_value)})

        converted_messages.append({"role": message.role, "content": blocks})
    return converted_messages

def _build_generation_kwargs(
    input_ids,
    attention_mask,
    max_toks: int,
    rep_pen: float,
    temp: float,
    top_p_val: float,
) -> dict[str, Any]:
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
    return gen_kwargs

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

    # Convert request messages to dictionaries. Text-only models flatten image
    # blocks instead of rejecting OpenAI-style multimodal payloads with 422.
    if USE_VISION:
        msg_dicts = _to_qwen_vl_messages(request.messages)
    else:
        msg_dicts = [{"role": m.role, "content": _content_to_text(m.content)} for m in request.messages]

    try:
        device = getattr(model, "device", next(model.parameters()).device)

        if USE_VISION:
            try:
                from qwen_vl_utils import process_vision_info
            except ImportError as import_error:
                raise HTTPException(
                    status_code=500,
                    detail="qwen-vl-utils is required for Qwen-VL image inputs."
                ) from import_error

            text = processor.apply_chat_template(
                msg_dicts,
                tokenize=False,
                add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(msg_dicts)
            inputs = processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            )
            inputs = inputs.to(device)

            do_sample = temp > 0
            vision_gen_kwargs = {
                "max_new_tokens": max_toks,
                "repetition_penalty": rep_pen,
                "do_sample": do_sample,
            }
            if do_sample:
                vision_gen_kwargs["temperature"] = temp
                vision_gen_kwargs["top_p"] = top_p_val

            with torch.no_grad():
                outputs = model.generate(**inputs, **vision_gen_kwargs)

            generated_ids = [
                output_ids[len(input_ids):]
                for input_ids, output_ids in zip(inputs.input_ids, outputs)
            ]
            response_text = processor.batch_decode(
                generated_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0]
            prompt_tokens = inputs.input_ids.shape[1]
            completion_tokens = len(generated_ids[0])
        else:
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
            input_ids = inputs.input_ids.to(device)
            attention_mask = inputs.attention_mask.to(device)
            gen_kwargs = _build_generation_kwargs(input_ids, attention_mask, max_toks, rep_pen, temp, top_p_val)

            with torch.no_grad():
                outputs = model.generate(**gen_kwargs)

            # Decode newly generated tokens only
            prompt_len = input_ids.shape[1]
            response_ids = outputs[0][prompt_len:]
            response_text = tokenizer.decode(response_ids, skip_special_tokens=True)
            prompt_tokens = prompt_len
            completion_tokens = len(response_ids)

        # Calculate token counts
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
