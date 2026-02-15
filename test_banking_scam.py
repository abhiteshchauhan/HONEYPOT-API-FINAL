"""
Banking Scam Test - Full JSON Payload + Response capture
"""
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/chat"
API_KEY = "honeypot-api-key-2024-secure"
HEADERS = {"Content-Type": "application/json", "x-api-key": API_KEY}
SESSION_ID = f"bank-scam-test-{int(time.time())}"

scammer_messages = [
    "Dear Customer, your SBI bank account has been temporarily suspended due to suspicious activity. Verify your identity immediately to avoid permanent closure.",
    "Please share your account number and registered mobile number for verification. This is urgent - your account will be permanently blocked within 2 hours.",
    "We need your OTP sent to your mobile number. Also transfer Rs 1 to this account 9876543210123456 (IFSC: SBIN0001234) to verify your identity.",
    "Sir your account will be blocked permanently. Send OTP now. You can also pay via UPI to sbi.verify@ybl for instant verification.",
    "This is your last warning. Call +91-9988776655 immediately or visit http://sbi-verify-account.fake.com to complete verification before deadline.",
]

conversation_history = []
separator = "=" * 70

for i, msg in enumerate(scammer_messages, 1):
    payload = {
        "sessionId": SESSION_ID,
        "message": {
            "sender": "scammer",
            "text": msg,
            "timestamp": int(time.time() * 1000),
        },
        "conversationHistory": conversation_history,
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN",
        },
    }

    print(f"\n{separator}")
    print(f"  MESSAGE {i} OF {len(scammer_messages)}")
    print(separator)
    print("\n--- REQUEST PAYLOAD ---")
    print(json.dumps(payload, indent=2))

    try:
        resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=60)
        resp_json = resp.json()
        print(f"\n--- RESPONSE (HTTP {resp.status_code}) ---")
        print(json.dumps(resp_json, indent=2))

        if resp.status_code == 200:
            reply = resp_json.get("reply", "")
            conversation_history.append(
                {"sender": "scammer", "text": msg, "timestamp": payload["message"]["timestamp"]}
            )
            conversation_history.append(
                {"sender": "user", "text": reply, "timestamp": int(time.time() * 1000)}
            )
    except Exception as e:
        print(f"\n--- ERROR ---\n{e}")

    if i < len(scammer_messages):
        time.sleep(2)

print(f"\n{separator}")
print("  BANKING SCAM TEST COMPLETE")
print(separator)
