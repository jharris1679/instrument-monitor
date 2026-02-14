#!/usr/bin/env python3
"""
Test MLX chat completions endpoint with detailed debugging.
"""
import requests
import time
import json
from pathlib import Path

API_URL = "http://localhost:8082/v1/chat/completions"
MODEL_ID = "/Users/studio/models/hf-cache/models--zai-org--GLM-4.7-Flash/snapshots/7dd20894a642a0aa287e9827cb1a1f7f91386b67"

print("=" * 80)
print("Test 1: Simple Chat Completion Request")
print("=" * 80)

headers = {
    "Content-Type": "application/json"
}

data = {
    "model": MODEL_ID,
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 50
}

print(f"URL: {API_URL}")
print(f"Model ID: {MODEL_ID}")
print(f"Headers: {headers}")
print(f"Data: {json.dumps(data, indent=2)}")
print()

try:
    print("Sending request...")
    start_time = time.time()

    response = requests.post(
        API_URL,
        headers=headers,
        json=data,
        timeout=30
    )

    elapsed = time.time() - start_time
    print(f"Response status code: {response.status_code}")
    print(f"Response time: {elapsed:.2f} seconds")
    print(f"Response headers: {dict(response.headers)}")
    print(f"Response text (first 500 chars):\n{response.text[:500]}")

    if response.status_code == 200:
        print("\n✓ Success! Response:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"Error response body:\n{response.text}")

except requests.exceptions.Timeout as e:
    print(f"\n✗ Request timed out: {e}")
except requests.exceptions.ConnectionError as e:
    print(f"\n✗ Connection error: {e}")
except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("Test 2: Verify Model Path Validity")
print("=" * 80)

model_path = Path(MODEL_ID)
print(f"Checking if model path exists: {model_path}")

if model_path.exists():
    print("✓ Model path exists")
    print(f"  Can read: {model_path.is_dir()}")
    if model_path.is_dir():
        files = list(model_path.glob("*"))
        print(f"  Contains {len(files)} files:")
        for f in files[:10]:
            print(f"    - {f.name}")
        if len(files) > 10:
            print(f"    ... and {len(files) - 10} more")
else:
    print("✗ Model path does NOT exist")
    print("  Server may not be able to load this model")

print("\n" + "=" * 80)
print("Test 3: Stream Request")
print("=" * 80)

data_stream = {
    "model": MODEL_ID,
    "messages": [
        {"role": "user", "content": "Count to 5"}
    ],
    "max_tokens": 100,
    "stream": True
}

print("Sending stream request...")

try:
    response = requests.post(
        API_URL,
        headers=headers,
        json=data_stream,
        timeout=60,
        stream=True
    )

    print(f"Response status code: {response.status_code}")

    if response.status_code == 200:
        print("✓ Stream succeeded! Receiving chunks:")
        chunk_count = 0
        for chunk in response.iter_content(chunk_size=128, decode_unicode=True):
            if chunk:
                chunk_count += 1
                print(f"Chunk {chunk_count}: {chunk[:100]}")
        print(f"Total chunks received: {chunk_count}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")