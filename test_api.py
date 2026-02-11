"""
Simple test script for Agentic Honey-Pot API
"""
import requests
import json
import time

# Configuration
API_URL = "http://localhost:8000/chat"
API_KEY = "honeypot-api-key-2024-secure"  # Your configured API key

# Test scenarios
test_scenarios = [
    {
        "name": "Bank Account Scam",
        "messages": [
            "Your bank account will be blocked today. Verify immediately.",
            "Share your account number and OTP to prevent suspension.",
            "Call this number for verification: +91-9876543210"
        ]
    },
    {
        "name": "UPI Fraud",
        "messages": [
            "Congratulations! You won 50,000 rupees.",
            "Send payment to winner@paytm to claim your prize.",
            "Visit http://claim-prize.fake.com to verify"
        ]
    },
    {
        "name": "Phishing Link",
        "messages": [
            "Your KYC is pending. Update now to avoid account closure.",
            "Click here: http://fake-bank-update.com/kyc",
            "For help, call +91-1234567890"
        ]
    }
]


def test_scenario(scenario, session_id):
    """Test a single scenario"""
    print(f"\n{'='*60}")
    print(f"Testing: {scenario['name']}")
    print(f"Session ID: {session_id}")
    print(f"{'='*60}\n")
    
    conversation_history = []
    
    for i, scammer_message in enumerate(scenario['messages'], 1):
        print(f"Message {i}:")
        print(f"Scammer: {scammer_message}")
        
        # Prepare request
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": scammer_message,
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": conversation_history,
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        # Send request
        try:
            response = requests.post(
                API_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                agent_reply = result.get("reply", "")
                print(f"Agent:   {agent_reply}")
                print(f"Status:  [OK] Success")
                
                # Update conversation history
                conversation_history.append({
                    "sender": "scammer",
                    "text": scammer_message,
                    "timestamp": payload["message"]["timestamp"]
                })
                conversation_history.append({
                    "sender": "user",
                    "text": agent_reply,
                    "timestamp": int(time.time() * 1000)
                })
            else:
                print(f"Status:  [ERROR] Error {response.status_code}")
                print(f"Response: {response.text}")
                break
        
        except requests.exceptions.RequestException as e:
            print(f"Status:  [ERROR] Request failed: {e}")
            break
        
        print()
        
        # Wait between messages
        if i < len(scenario['messages']):
            time.sleep(2)
    
    print(f"{'='*60}\n")


def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Health check passed: {result}")
            return True
        else:
            print(f"[ERROR] Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Health check error: {e}")
        return False


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("Agentic Honey-Pot API - Test Suite")
    print("="*60)
    
    # Test health first
    if not test_health():
        print("\n⚠ API is not healthy. Make sure the server is running.")
        print("   Run: uvicorn app.main:app --reload")
        return
    
    print("\n")
    
    # Run test scenarios
    for i, scenario in enumerate(test_scenarios, 1):
        session_id = f"test-session-{int(time.time())}-{i}"
        test_scenario(scenario, session_id)
        
        # Wait between scenarios
        if i < len(test_scenarios):
            print("Waiting 3 seconds before next scenario...\n")
            time.sleep(3)
    
    print("="*60)
    print("Test suite completed!")
    print("="*60)


if __name__ == "__main__":
    main()
