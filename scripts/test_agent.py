import sys
import json
import os
import requests

DEFAULT_AGENT_URL = "http://127.0.0.1:8000/agent/invoke"
DEFAULT_TIMEOUT_SECONDS = 120

def get_timeout_seconds() -> float:
    raw_value = os.getenv("AGENT_TEST_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        timeout_seconds = float(raw_value)
        if timeout_seconds <= 0:
            raise ValueError
        return timeout_seconds
    except ValueError:
        print(
            f"Warning: invalid AGENT_TEST_TIMEOUT_SECONDS={raw_value!r}; "
            f"using {DEFAULT_TIMEOUT_SECONDS} seconds."
        )
        return DEFAULT_TIMEOUT_SECONDS

def test_agent_invoke():
    url = os.getenv("AGENT_API_URL") or os.getenv("AGENT_TEST_URL") or DEFAULT_AGENT_URL
    timeout_seconds = get_timeout_seconds()
    payload = {
        "query": "A batch of machined parts has an outer diameter deviation of +0.05mm. The machine is CNC-01, the material is 45 steel, and the cutting tool was recently replaced. Please analyze possible causes and provide troubleshooting steps.",
        "user_id": "demo_user",
        "context": {}
    }
    headers = {
        "Content-Type": "application/json"
    }

    print(f"Sending POST request to {url}...")
    print(f"Client timeout: {timeout_seconds:g} seconds")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout_seconds)
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            print("--- AGENT RESPONSE ---")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("----------------------")
        else:
            print(f"Error: Server returned non-200 status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print(f"Error: Connection refused. Is the FastAPI server running at {url}?")
        sys.exit(1)
    except requests.exceptions.ReadTimeout:
        print(
            f"Error: request timed out after {timeout_seconds:g} seconds. "
            "The full LangGraph flow makes multiple LLM calls, so local GPU inference can exceed short client timeouts."
        )
        print("Increase AGENT_TEST_TIMEOUT_SECONDS or reduce QWEN_MAX_TOKENS / llm_max_tokens for faster tests.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_agent_invoke()
