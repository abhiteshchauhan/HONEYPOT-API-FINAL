"""
Multiple Fraud Types Test - Full JSON Payload + Response capture
Tests different scam categories: Banking, UPI, Lottery, Tax, Job, Romance, Tech Support
"""
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/chat"
API_KEY = "honeypot-api-key-2024-secure"
HEADERS = {"Content-Type": "application/json", "x-api-key": API_KEY}

# Different fraud scenarios
fraud_scenarios = {
    "Banking Fraud": [
        "URGENT: Your HDFC account has been compromised. Verify immediately by calling +91-9123456789.",
        "We detected suspicious activity. Share your CVV and card number to secure your account.",
        "Your account will be frozen. Transfer Rs 5000 to account 1234567890123456 (IFSC: HDFC0001234) for reactivation."
    ],
    
    "UPI Scam": [
        "Congratulations! You won Rs 1,00,000 in Google Pay lottery. Send Rs 500 to winner2024@paytm to claim.",
        "Refund of Rs 8,500 pending. Share your UPI PIN to process the refund instantly.",
        "Pay Rs 1 to verify.upi@oksbi for account verification and receive cashback."
    ],
    
    "Lottery/Prize Scam": [
        "You are selected as lucky winner of iPhone 15 Pro. Pay Rs 2000 shipping to claim your prize.",
        "KBC Lottery Winner! Call +91-8765432109 and pay Rs 5000 processing fee to receive 25 lakhs.",
        "Flipkart Anniversary Winner! Click http://flipkart-prize.scam.com and enter your bank details."
    ],
    
    "Tax/Government Scam": [
        "Income Tax Notice: Pay pending tax of Rs 15,000 immediately or face legal action. Call +91-7654321098.",
        "Aadhaar card will be blocked. Update KYC at http://aadhaar-update.fake.in within 24 hours.",
        "GST refund of Rs 12,000 approved. Share PAN and bank account to receive refund."
    ],
    
    "Job/Employment Scam": [
        "Congratulations! Selected for Google Work From Home job. Pay Rs 3000 registration fee to hr.google@gmail.com",
        "Earn Rs 50,000/month from home. Send Rs 5000 to training.jobs@paytm for training materials.",
        "Amazon hiring! Pay security deposit of Rs 10,000 to account 9988776655443322 (IFSC: SBIN0005678)."
    ],
    
    "Romance/Dating Scam": [
        "Hi dear, I'm Sarah from USA. I sent you $5000 gift but customs needs Rs 8000. Can you help?",
        "My love, I'm stuck at airport. Send Rs 15,000 to +91-9876543210 for emergency ticket.",
        "I want to meet you but need visa fee Rs 20,000. Transfer to visa.help@ybl urgently."
    ],
    
    "Tech Support Scam": [
        "Microsoft Security Alert! Your Windows is infected. Call +91-8899776655 immediately for support.",
        "Your computer has virus. Pay Rs 4999 to techsupport@paytm for antivirus activation.",
        "Google account hacked! Verify at http://google-security.fake.com or lose all data."
    ],
    
    "Parcel/Delivery Scam": [
        "Your Amazon parcel is held at customs. Pay Rs 1200 to delivery.amazon@oksbi for release.",
        "FedEx: Package delivery failed. Click http://fedex-track.scam.in and pay Rs 800 redelivery fee.",
        "India Post: Parcel waiting. Call +91-7788996655 and pay Rs 500 for home delivery."
    ]
}

def test_fraud_scenario(fraud_type, messages):
    """Test a single fraud scenario"""
    session_id = f"fraud-test-{fraud_type.replace(' ', '-').lower()}-{int(time.time())}"
    
    print(f"\n{'='*80}")
    print(f"  TESTING: {fraud_type.upper()}")
    print(f"  Session ID: {session_id}")
    print(f"{'='*80}\n")
    
    conversation_history = []
    
    for i, msg in enumerate(messages, 1):
        payload = {
            "sessionId": session_id,
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

        print(f"--- MESSAGE {i}/{len(messages)} ---")
        print(f"Scammer: {msg}\n")

        try:
            resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=60)
            resp_json = resp.json()
            
            if resp.status_code == 200:
                print(f"Agent: {resp_json.get('reply', '')}")
                print(f"Scam Detected: {resp_json.get('scamDetected', False)}")
                print(f"Messages Exchanged: {resp_json.get('totalMessagesExchanged', 0)}")
                
                intel = resp_json.get('extractedIntelligence', {})
                if any(intel.values()):
                    print(f"\nExtracted Intelligence:")
                    if intel.get('bankAccounts'):
                        print(f"  - Bank Accounts: {intel['bankAccounts']}")
                    if intel.get('upiIds'):
                        print(f"  - UPI IDs: {intel['upiIds']}")
                    if intel.get('phoneNumbers'):
                        print(f"  - Phone Numbers: {intel['phoneNumbers']}")
                    if intel.get('phishingLinks'):
                        print(f"  - Phishing Links: {intel['phishingLinks']}")
                
                reply = resp_json.get('reply', '')
                conversation_history.append(
                    {"sender": "scammer", "text": msg, "timestamp": payload["message"]["timestamp"]}
                )
                conversation_history.append(
                    {"sender": "user", "text": reply, "timestamp": int(time.time() * 1000)}
                )
            else:
                print(f"ERROR: HTTP {resp.status_code}")
                print(f"Response: {resp.text}")
                break
                
        except Exception as e:
            print(f"ERROR: {e}")
            break

        print()
        if i < len(messages):
            time.sleep(1.5)
    
    print(f"{'='*80}\n")

def main():
    """Run all fraud scenario tests"""
    print("\n" + "="*80)
    print("  HONEYPOT API - MULTIPLE FRAUD TYPES TEST SUITE")
    print("="*80)
    
    for fraud_type, messages in fraud_scenarios.items():
        test_fraud_scenario(fraud_type, messages)
        time.sleep(2)
    
    print("="*80)
    print("  ALL FRAUD TESTS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    main()
