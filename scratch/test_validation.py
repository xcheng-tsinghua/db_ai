from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

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

# Test payload with content as None
payload = {
    "model": "qwen7b",
    "messages": [
        {"role": "system", "content": None},
        {"role": "user", "content": "hello"}
    ],
    "temperature": 0.2,
    "max_tokens": 2048
}

try:
    req = ChatCompletionRequest(**payload)
    print("Validation passed!")
    print(req)
except Exception as e:
    print("Validation failed!")
    print(e)


