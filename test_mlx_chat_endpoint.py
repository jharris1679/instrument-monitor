import httpx
import json

def test_chat_completions():
    """Test the /v1/chat/completions endpoint with the local MLX server"""

    url = "http://localhost:8082/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-token"  # Fake token since auth not configured
    }

    # Simple test payload to check if endpoint works
    payload = {
        "model": "glm-4.7-flash",  # Try with model name
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello from MLX!'"
            }
        ],
        "stream": False,
        "max_tokens": 50
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            print(f"Testing {url}...")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            response = client.post(url, json=payload, headers=headers)

            print(f"\nResponse status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response body: {response.text}")

            if response.status_code == 200:
                # Convert JSON response to dictionary for inspection
                data = response.json()
                print("\n✅ Success! Response structure:")
                print(json.dumps(data, indent=2))
                return True
            else:
                print(f"\n❌ Failed with status {response.status_code}")
                print(f"Error response: {response.text}")
                return False

    except Exception as e:
        print(f"\n❌ Exception occurred: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    success = test_chat_completions()
    exit(0 if success else 1)