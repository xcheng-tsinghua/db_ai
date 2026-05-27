import os
import sys
from openai import OpenAI, APIConnectionError, APIError

# Try loading from .env if present in parent directory
try:
    from dotenv import load_dotenv
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(parent_dir, ".env"))
except ImportError:
    pass

def test_qwen():
    # Read environment configurations or default
    base_url = os.getenv("QWEN_BASE_URL", "http://localhost:8001/v1")
    api_key = os.getenv("QWEN_API_KEY", "EMPTY")
    model = os.getenv("QWEN_MODEL", "qwen14b")
    
    print(f"Testing OpenAI-compatible Qwen API:")
    print(f"  URL:   {base_url}")
    print(f"  Model: {model}")
    print(f"  Key:   {api_key}\n")
    
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )
    
    messages = [
        {
            "role": "user",
            "content": "Briefly explain what vLLM is and why it is useful for serving Qwen models."
        }
    ]
    
    print("Sending Chat Completion Request...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            top_p=0.8,
            max_tokens=512
        )
        print("\n--- RESPONSE FROM QWEN ---")
        if response.choices:
            print(response.choices[0].message.content)
        else:
            print("Received empty choices in response.")
        print("--------------------------")
        print("\nAPI test succeeded!")
    except APIConnectionError as e:
        print(f"\nConnection Error: Cannot connect to server at {base_url}.")
        print("Please check if your vLLM or Ollama instance is running and healthy.")
        print(f"Details: {e}")
        sys.exit(1)
    except APIError as e:
        print(f"\nAPI Error returned by server: Code={e.code}, Message={e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during request: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_qwen()
