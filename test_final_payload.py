"""
Test: Send 10 scam messages and print the final JSON payload from /results
"""
import requests
import json
import time
import uuid

API_URL = "https://myproject2-vert-one.vercel.app"
API_KEY = "honeypot-api-key-2024-secure"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

# 10 scam messages that progressively reveal fake data
SCAM_MESSAGES = [
    "URGENT: Your SBI bank account has been compromised and will be blocked in 2 hours.",
    "To prevent suspension, verify your identity immediately. This is SBI fraud prevention team.",
    "Your account number 1234567890123456 is flagged for suspicious activity.",
    "Call our helpline at +91-9876543210 to speak with our security officer.",
    "You can also verify online at http://sbi-secure-verify.com/kyc",
    "Send a small verification amount of Rs.1 to our UPI: scammer.fraud@fakebank",
    "Your OTP has been sent. Share it with our officer to confirm your identity.",
    "We also need your registered email to send the verification link.",
    "Time is running out - account will be permanently blocked in 30 minutes.",
    "Final warning: Complete verification now or lose all your funds permanently."
]


def run_test():
    session_id = str(uuid.uuid4())
    conversation_history = []

    print(f"\n{'='*60}")
    print(f"Session ID: {session_id}")
    print(f"API:        {API_URL}")
    print(f"{'='*60}\n")

    for i, msg in enumerate(SCAM_MESSAGES, 1):
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": msg,
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": conversation_history,
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
        }

        try:
            r = requests.post(f"{API_URL}/chat", json=payload, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                reply = r.json().get("reply", "")
                print(f"[{i:02d}] Scammer: {msg[:70]}...")
                print(f"      Agent:   {reply}")
                conversation_history.append({
                    "sender": "scammer",
                    "text": msg,
                    "timestamp": int(time.time() * 1000)
                })
                conversation_history.append({
                    "sender": "user",
                    "text": reply,
                    "timestamp": int(time.time() * 1000)
                })
            else:
                print(f"[{i:02d}] ERROR {r.status_code}: {r.text}")
                break
        except Exception as e:
            print(f"[{i:02d}] Request failed: {e}")
            break

        time.sleep(1)

    print(f"\n{'='*60}")
    print("FINAL JSON PAYLOAD (/results)")
    print(f"{'='*60}\n")

    try:
        r = requests.get(f"{API_URL}/results/{session_id}", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            result = r.json()
            print(json.dumps(result, indent=2))

            print(f"\n{'='*60}")
            print("SCORE ESTIMATE")
            print(f"{'='*60}")
            score = 0

            # Scam Detection (20pts)
            if result.get("scamDetected"):
                print("[+20] scamDetected = True")
                score += 20
            else:
                print("[ +0] scamDetected = False")

            # Intelligence (40pts)
            intel = result.get("extractedIntelligence", {})
            fake_checks = {
                "bankAccounts":  "1234567890123456",
                "upiIds":        "scammer.fraud@fakebank",
                "phoneNumbers":  "9876543210",
                "phishingLinks": "sbi-secure-verify.com",
            }
            for field, value in fake_checks.items():
                extracted = intel.get(field, [])
                if any(value in str(v) for v in extracted):
                    print(f"[+10] {field} extracted: {extracted}")
                    score += 10
                else:
                    print(f"[ +0] {field} NOT found (got: {extracted})")

            # Engagement Quality (20pts)
            metrics = result.get("engagementMetrics", {})
            duration = metrics.get("engagementDurationSeconds", 0)
            messages = metrics.get("totalMessagesExchanged", 0)
            if duration > 0:
                print(f"[ +5] duration > 0  ({duration}s)")
                score += 5
            if duration > 60:
                print(f"[ +5] duration > 60 ({duration}s)")
                score += 5
            if messages > 0:
                print(f"[ +5] messages > 0  ({messages})")
                score += 5
            if messages >= 5:
                print(f"[ +5] messages >= 5 ({messages})")
                score += 5

            # Response Structure (20pts)
            for field in ["status", "scamDetected", "extractedIntelligence"]:
                if field in result:
                    print(f"[ +5] field present: {field}")
                    score += 5
            for field in ["engagementMetrics", "agentNotes"]:
                if result.get(field):
                    print(f"[+2.5] field present: {field}")
                    score += 2.5

            print(f"\nESTIMATED SCORE: {score}/100")
        else:
            print(f"ERROR {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Failed to fetch results: {e}")


if __name__ == "__main__":
    run_test()
