#!/usr/bin/env python3
"""
Diagnostic test for httpx MLX server connection.
"""
import httpx
import json
import time

API_URL = "http://localhost:8082/v1/chat/completions"
MODEL_ID = "/Users/studio/models/hf-cache/models--zai-org--GLM-4.7-Flash/snapshots/7dd20894a642a0aa287e9827cb1a1f7f91386b67"

print("=" * 80)
print("Diagnosing httpx MLX Server Connection")
print("=" * 80)
print(f"URL: {API_URL}")
print(f"Model ID: {MODEL_ID}")
print()

payload = {
    "model": MODEL_ID,
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 50
}

print("Test 1: Direct httpx.post() call (same as insight_generator.py)")
print("-" * 80)

try:
    print(f"Payload: {json.dumps(payload, indent=2)}")
    response = httpx.post(
        API_URL,
        json=payload,
        timeout=120
    )
    print(f"✓ Response received: {response.status_code}")
    print(f"Response headers: {response.headers}")

except httpx.TimeoutException as e:
    print(f"✗ TimeoutException: {e}")
except httpx.ConnectionError as e:
    print(f"✗ ConnectionError (Cause: {type(e.__cause__).__name__}): {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("Test 2: httpx.Client() (persistent connection)")
print("-" * 80)

try:
    with httpx.Client() as client:
        response = client.post(
            API_URL,
            json=payload,
            timeout=120
        )
        print(f"✓ Response received: {response.status_code}")
except Exception as e:
    print(f"✗ {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("Test 3: httpx.AsyncClient() (async connection)")
print("-" * 80)

import asyncio

async def test_async():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_URL,
                json=payload,
                timeout=120
            )
            print(f"✓ Response received: {response.status_code}")
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_async())

print()
print("Test 4: Timeout variations")
print("-" * 80)

for timeout in [30, 60, 120, 180]:
    try:
        response = httpx.post(
            API_URL,
            json=payload,
            timeout=timeout
        )
        print(f"✓ Timeout {timeout}s: Success (status {response.status_code})")
    except Exception as e:
        print(f"✗ Timeout {timeout}s: {type(e).__name__}: {e}")

print()
print("Test 5: SSL verification on/off (if using HTTPS)")
print("-" * 80)

try:
    # This test is irrelevant for HTTP, but if/when moving to HTTPS:
    response = httpx.post(API_URL, json=payload, timeout=120, verify=False)
    print(f"Response with verify=False: {response.status_code}")
except Exception as e:
    print(f"✗ verify=False: {type(e).__name__}: {e}")

print()
print("=" * 80)
print("Diagnostic complete")
print("=" * 80)