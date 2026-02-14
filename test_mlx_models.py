import httpx
import json

def test_chat_completions_with_different_models():
    """Test various model names that might work with the local MLX server"""

    url = "http://localhost:8082/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-token"
    }

    # Try different model names
    test_models = [
        "glm4-flash",               # Different naming convention
        "glm-4-flash",              # Alternative
        "glm-4.7-flash",            # Original from .env
        "glm-4-fast",               # Fast variant
        "fast-glm",                 # Simplified name
        "fast-glm-4.7",             # Other variation
    ]

    for model_name in test_models:
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'Hello!'"
                }
            ],
            "stream": False,
            "max_tokens": 30
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                print(f"\n{'='*60}")
                print(f"Testing model: {model_name}")
                print(f"{'='*60}")

                response = client.post(url, json=payload, headers=headers)

                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0]['message']['content']
                        print(f"✅ Success! Model '{model_name}' accepted")
                        print(f"Response: {content[:100]}")
                    else:
                        print(f"Model accepted but no content in response")
                        print(f"Full response: {json.dumps(data, indent=2)}")
                else:
                    print(f"❌ Failed")
                    print(f"Error: {response.text[:500]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    test_chat_completions_with_different_models()