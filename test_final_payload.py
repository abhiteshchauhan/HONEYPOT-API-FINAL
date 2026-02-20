"""
Test: Send 10 scam messages and print the final JSON payload from /results
"""
import requests
import json
import time
import uuid

API_URL = "http://localhost:8000"
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
            r = requests.post(f"{API_URL}/chat", json=payload, headers=HEADERS, timeout=60)
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

    # Wait briefly for Vercel to finish processing last message
    time.sleep(3)

    result = None
    for attempt in range(1, 4):
        try:
            print(f"Fetching /results (attempt {attempt}/3)...")
            r = requests.get(f"{API_URL}/results/{session_id}", headers=HEADERS, timeout=60)
            if r.status_code == 200:
                result = r.json()
                break
            else:
                print(f"  Got {r.status_code}: {r.text}")
        except Exception as e:
            print(f"  Attempt {attempt} failed: {e}")
        if attempt < 3:
            time.sleep(5)

    if result is None:
        print("Could not fetch /results after 3 attempts.")
        return

    print(json.dumps(result, indent=2))

    print(f"\n{'='*60}")
    print("SCORE ESTIMATE (New Scoring System)")
    print(f"{'='*60}")
    score = 0

    # 1. Scam Detection (20pts)
    print("\n[1] SCAM DETECTION (20pts)")
    if result.get("scamDetected"):
        print("  [+20] scamDetected = True")
        score += 20
    else:
        print("  [ +0] scamDetected = False")

    # 2. Intelligence Extraction (30pts — 30/N per item, N=4 fake fields in this test)
    print("\n[2] INTELLIGENCE EXTRACTION (30pts)")
    intel = result.get("extractedIntelligence", {})
    fake_checks = {
        "bankAccounts":  "1234567890123456",
        "upiIds":        "scammer.fraud@fakebank",
        "phoneNumbers":  "9876543210",
        "phishingLinks": "sbi-secure-verify.com",
    }
    pts_per_item = 30 / len(fake_checks)
    for field, value in fake_checks.items():
        extracted = intel.get(field, [])
        if any(value in str(v) for v in extracted):
            print(f"  [+{pts_per_item:.1f}] {field}: {extracted}")
            score += pts_per_item
        else:
            print(f"  [ +0] {field} NOT found (got: {extracted})")

    # 3. Conversation Quality (30pts) - evaluated by GUVI from actual conversation content
    print("\n[3] CONVERSATION QUALITY (30pts)")
    messages_count = result.get("totalMessagesExchanged", 0)
    turns = messages_count // 2  # Each turn = 1 scammer msg + 1 agent reply
    print(f"  Estimated turns from messages: {turns} (GUVI evaluates actual conversation)")
    if turns >= 8:
        print(f"  [ +8] turnCount >= 8 (est. {turns})")
        score += 8
    elif turns >= 6:
        print(f"  [ +6] turnCount >= 6 (est. {turns})")
        score += 6
    elif turns >= 4:
        print(f"  [ +3] turnCount >= 4 (est. {turns})")
        score += 3
    print(f"  [+22] questions/redflags/elicitation (GUVI evaluates from conversation - estimated full score)")
    score += 22

    # 4. Engagement Quality (10pts)
    print("\n[4] ENGAGEMENT QUALITY (10pts)")
    metrics = result.get("engagementMetrics", {})
    duration = metrics.get("engagementDurationSeconds", 0)
    messages = metrics.get("totalMessagesExchanged", 0)
    if duration > 0:
        print(f"  [ +1] duration > 0 ({duration}s)")
        score += 1
    if duration > 60:
        print(f"  [ +2] duration > 60 ({duration}s)")
        score += 2
    if duration > 180:
        print(f"  [ +1] duration > 180 ({duration}s)")
        score += 1
    if messages > 0:
        print(f"  [ +2] messages > 0 ({messages})")
        score += 2
    if messages >= 5:
        print(f"  [ +3] messages >= 5 ({messages})")
        score += 3
    if messages >= 10:
        print(f"  [ +1] messages >= 10 ({messages})")
        score += 1

    # 5. Response Structure (10pts)
    print("\n[5] RESPONSE STRUCTURE (10pts)")
    req_fields = {"sessionId": 2, "scamDetected": 2, "extractedIntelligence": 2}
    opt_fields = {
        "totalMessagesExchanged and engagementDurationSeconds": 1,
        "agentNotes": 1, "scamType": 1, "confidenceLevel": 1
    }
    for field, pts in req_fields.items():
        if field in result:
            print(f"  [+{pts}] {field} present")
            score += pts
        else:
            print(f"  [+0] {field} MISSING")
    metrics_ok = result.get("engagementMetrics", {}).get("totalMessagesExchanged") is not None \
        and result.get("engagementMetrics", {}).get("engagementDurationSeconds") is not None
    if metrics_ok:
        print(f"  [+1] totalMessagesExchanged + engagementDurationSeconds present")
        score += 1
    if result.get("agentNotes"):
        print(f"  [+1] agentNotes present")
        score += 1
    if result.get("scamType") and result.get("scamType") != "Unknown":
        print(f"  [+1] scamType present: {result.get('scamType')}")
        score += 1
    if result.get("confidenceLevel"):
        print(f"  [+1] confidenceLevel present: {result.get('confidenceLevel')}")
        score += 1

    print(f"\n{'='*60}")
    print(f"ESTIMATED SCORE: {score:.1f}/100")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_test()
