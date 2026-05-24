import sys
import json
import requests

def test_agent_invoke():
    url = "http://localhost:8000/agent/invoke"
    payload = {
        "query": "A batch of machined parts has an outer diameter deviation of +0.05mm. The machine is CNC-01, the material is 45 steel, and the cutting tool was recently replaced. Please analyze possible causes and provide troubleshooting steps.",
        "user_id": "demo_user",
        "context": {}
    }
    headers = {
        "Content-Type": "application/json"
    }

    print(f"Sending POST request to {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
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
        print(f"Error: Connection refused. Is the FastAPI server running on http://localhost:8000?")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_agent_invoke()
