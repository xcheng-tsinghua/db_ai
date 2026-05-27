import os
import requests
import json

base_url = os.getenv("QWEN_BASE_URL", "http://127.0.0.1:8001/v1")
model_name = os.getenv("QWEN_MODEL", "qwen7b")

print(f"Testing local Transformers Qwen Server at: {base_url}")
print(f"Testing model: {model_name}\n")

# 1. Test GET /v1/models
models_url = f"{base_url.rstrip('/')}/models"
try:
    print(f"Sending GET request to {models_url}...")
    response = requests.get(models_url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    else:
        print(f"Failed response: {response.text}")
except Exception as e:
    print(f"Failed to connect to /models endpoint: {e}")

print("-" * 50)

# 2. Test POST /v1/chat/completions
completions_url = f"{base_url.rstrip('/')}/chat/completions"
payload = {
    "model": model_name,
    "messages": [
        {
            "role": "user",
            "content": "Briefly explain what Qwen is."
        }
    ],
    "temperature": 0.2,
    "top_p": 0.8,
    "max_tokens": 512,
    "stream": False
}

try:
    print(f"Sending POST request to {completions_url}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    response = requests.post(completions_url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Response from server:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Server returned error response: {response.text}")
except Exception as e:
    print(f"Failed to connect to /chat/completions endpoint: {e}")
