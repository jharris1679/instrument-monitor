import httpx
import sys

def check_mlx_server_config():
    """Check what the MLX server expects"""

    try:
        # Check for models list endpoint
        print("Checking /v1/models endpoint...", file=sys.stderr)
        response = httpx.get("http://localhost:8082/v1/models", timeout=10.0)
        print(f"Status: {response.status_code}", file=sys.stderr)
        if response.status_code == 200:
            print(f"Success! Models: {response.text[:500]}", file=sys.stderr)
            return

        # Try health endpoints
        print("Checking health endpoints...", file=sys.stderr)
        for endpoint in ["/health", "/api/health", "/status"]:
            try:
                response = httpx.get(f"http://localhost:8082{endpoint}", timeout=10.0)
                print(f"{endpoint}: {response.status_code}", file=sys.stderr)
                if response.status_code == 200:
                    print(f"Success with {endpoint}: {response.text[:200]}", file=sys.stderr)
            except Exception as e:
                print(f"{endpoint}: Error - {e}", file=sys.stderr)

        # Test chat completion with no model
        print("Testing chat completion with no model name...", file=sys.stderr)
        payload = {
            "messages": [{"role": "user", "content": "Say hello"}],
            "stream": False,
            "max_tokens": 20
        }

        response = httpx.post("http://localhost:8082/v1/chat/completions", json=payload, timeout=30.0)
        print(f"Status: {response.status_code}", file=sys.stderr)
        print(f"Response: {response.text[:500]}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    check_mlx_server_config()