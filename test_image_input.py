"""
Test: Send the project's sample PNG image (BHIM UPI QR code) to /chat via the
existing JSON endpoint.

The image is base64-encoded and placed in message.text as a data URI:
    "text": "data:image/png;base64,<b64data>"

The ImageHandler in app/services/image_handler.py detects this automatically
and converts it to a plain-text description before the rest of the pipeline runs.

Usage:
    python test_image_input.py
"""
import base64
import json
import time
import uuid
import requests

API_URL = "http://localhost:8000"
API_KEY = "honeypot-api-key-2024-secure"
IMAGE_PATH = "5fbbfe4c-af2f-42f1-b5b4-0117981a400d.jpg"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}


def load_image_as_data_uri(path: str) -> str:
    """Read a PNG file and return it as a data URI string."""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def run_test():
    session_id = str(uuid.uuid4())

    print(f"\n{'='*60}")
    print("TEST: PNG Image Input via /chat (data URI in text field)")
    print(f"Image : {IMAGE_PATH}")
    print(f"Session: {session_id}")
    print(f"API   : {API_URL}")
    print(f"{'='*60}\n")

    # --- Load image ---
    try:
        data_uri = load_image_as_data_uri(IMAGE_PATH)
        print(f"[OK] Image loaded — data URI length: {len(data_uri)} chars")
    except FileNotFoundError:
        print(f"[FAIL] Image file not found: {IMAGE_PATH}")
        print("       Make sure you run this test from the project root directory.")
        return

    conversation_history = []

    # --- Test 1: Image-only message (no accompanying text) ---
    print("\n[Test 1] Image-only message — PNG placed directly in text field")
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": data_uri,
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [],
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"}
    }

    try:
        r = requests.post(f"{API_URL}/chat", json=payload, headers=HEADERS, timeout=60)
        if r.status_code == 200:
            data = r.json()
            print(f"  Status : {data.get('status')}")
            print(f"  Reply  : {data.get('reply')}")
            assert data.get("status") == "success", "Expected status=success"
            assert data.get("reply"), "Expected non-empty reply"
            print("  [PASS] Image-only message handled correctly")
            conversation_history.append({
                "sender": "scammer",
                "text": "[image: BHIM UPI QR code]",
                "timestamp": int(time.time() * 1000)
            })
            conversation_history.append({
                "sender": "user",
                "text": data.get("reply", ""),
                "timestamp": int(time.time() * 1000)
            })
        else:
            print(f"  [FAIL] HTTP {r.status_code}: {r.text}")
            return
    except Exception as e:
        print(f"  [FAIL] Request error: {e}")
        return

    time.sleep(1)

    # --- Test 2: Follow-up plain-text message in same session ---
    print("\n[Test 2] Follow-up plain-text message in the same session")
    payload2 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Scan the QR code and send Rs.500 to sharma@upi to verify your account.",
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": conversation_history,
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"}
    }

    try:
        r = requests.post(f"{API_URL}/chat", json=payload2, headers=HEADERS, timeout=60)
        if r.status_code == 200:
            data = r.json()
            print(f"  Status : {data.get('status')}")
            print(f"  Reply  : {data.get('reply')}")
            assert data.get("status") == "success", "Expected status=success"
            assert data.get("reply"), "Expected non-empty reply"
            print("  [PASS] Follow-up text message handled correctly")
        else:
            print(f"  [FAIL] HTTP {r.status_code}: {r.text}")
    except Exception as e:
        print(f"  [FAIL] Request error: {e}")

    time.sleep(3)

    # --- Fetch final results ---
    print(f"\n{'='*60}")
    print("FINAL RESULTS (/results)")
    print(f"{'='*60}")
    try:
        r = requests.get(
            f"{API_URL}/results/{session_id}",
            headers=HEADERS,
            timeout=60
        )
        if r.status_code == 200:
            result = r.json()
            print(json.dumps(result, indent=2))

            print(f"\n--- Key fields ---")
            print(f"  scamDetected        : {result.get('scamDetected')}")
            print(f"  scamType            : {result.get('scamType')}")
            print(f"  confidenceLevel     : {result.get('confidenceLevel')}")
            intel = result.get("extractedIntelligence", {})
            print(f"  upiIds              : {intel.get('upiIds', [])}")
            print(f"  phishingLinks       : {intel.get('phishingLinks', [])}")
            print(f"  suspiciousKeywords  : {intel.get('suspiciousKeywords', [])}")
        else:
            print(f"  [FAIL] HTTP {r.status_code}: {r.text}")
    except Exception as e:
        print(f"  [FAIL] Request error: {e}")

    print(f"\n{'='*60}")
    print("Image input test complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_test()
