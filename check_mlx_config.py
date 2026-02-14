import httpx

def check_mlx_server_config():
    """Check what the MLX server expects or allows"""

    url = "http://localhost:8082/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-token"
    }

    # First, let's check if there's documentation or info about the server
    print("Checking MLX server info...")

    # Try with no model name or an empty string
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello!'"
            }
        ],
        "stream": False,
        "max_tokens": 30
    }

    # What happens if we don't include a model name at all?
    print("\n1. Testing with no model name:")
    print("Payload:", json.dumps(payload, indent=2))
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, json=payload, headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ Server works - check server logs for which model loaded")
                print(f"Response: {response.text[:200]}")
            else:
                print(f"❌ Failed: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")

    # Try a different approach - check for model list endpoint
    print("\n2. Checking for alternative endpoints...")

    try:
        # Some servers expose a models list endpoint
        models_url = "http://localhost:8082/v1/models"
        response = httpx.get(models_url, timeout=10.0)
        print(f"GET {models_url}: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Available models:")
            try:
                data = response.json()
                print(json.dumps(data, indent=2))
            except:
                print(response.text[:500])
    except:
        print("No /models endpoint available")

    # Try common OpenAI-compatible endpoints
    for endpoint in [
        "/health",
        "/api/health",
        "/status",
        "/system_info",
    ]:
        try:
            response = httpx.get(f"http://localhost:8082{endpoint}", timeout=10.0)
            print(f"\nGET {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ Endpoint available")
                print(f"Response: {response.text[:200]}")
        except:
            pass


if __name__ == "__main__":
    pass