import httpx
import json

def test_model_with_full_path():
    """Test the MLX server with the actual model path"""

    model_path = "/Users/studio/models/hf-cache/models--zai-org--GLM-4.7-Flash/snapshots/7dd20894a642a0aa287e9827cb1a1f7f91386b67"

    url = f"http://localhost:8082/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-token"
    }

    payload = {
        "model": model_path,
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
        with httpx.Client(timeout=60.0) as client:
            print(f"Testing with model path: {model_path}")
            print(f"Payload: {json.dumps(payload, indent=2)}\n")

            response = client.post(url, json=payload, headers=headers)

            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}\n")

            if response.status_code == 200:
                data = response.json()
                print("✅ Success! Model accepted")
                print(f"\nFull response:")
                print(json.dumps(data, indent=2))
                return True
            else:
                print(f"\n❌ Failed with status {response.status_code}")
                print(f"Error response: {response.text}")
                return False

    except Exception as e:
        print(f"\n❌ Exception occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_model_with_full_path()
    exit(0 if success else 1)