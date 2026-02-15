"""
Test the typing delay functionality
"""
import asyncio
import httpx
import time

API_URL = "http://localhost:8000/chat"
API_KEY = "honeypot-api-key-2024-secure"

async def test_delay():
    """Test that delay is proportional to response length"""
    
    test_messages = [
        {
            "name": "Short message",
            "text": "Hi",
            "expected_delay": "~2.0s (minimum)"
        },
        {
            "name": "Medium message",
            "text": "Your bank account will be blocked. Call us now at 9876543210",
            "expected_delay": "~2.5-3.0s"
        },
        {
            "name": "Long message",
            "text": "Congratulations! You've won a brand new iPhone 15 Pro! To claim your prize, contact us immediately at 9876543210 or visit our website. This is a limited time offer! Only 5 winners selected. Call now to verify your details and get free delivery.",
            "expected_delay": "~5-6s"
        }
    ]
    
    print("=" * 70)
    print("TESTING TYPING DELAY FUNCTIONALITY")
    print("=" * 70)
    print("\nDelay Formula: len(response) / 50 chars/sec")
    print("Min: 2.0s, Max: 8.0s, Jitter: ±0.5s\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, test in enumerate(test_messages, 1):
            print(f"\n--- Test {i}: {test['name']} ---")
            print(f"Scammer: {test['text'][:60]}{'...' if len(test['text']) > 60 else ''}")
            print(f"Expected delay: {test['expected_delay']}")
            
            payload = {
                "sessionId": f"delay-test-{i}",
                "message": {
                    "sender": "scammer",
                    "text": test['text'],
                    "timestamp": int(time.time() * 1000)
                },
                "conversationHistory": []
            }
            
            try:
                start_time = time.time()
                
                response = await client.post(
                    API_URL,
                    json=payload,
                    headers={
                        "X-API-Key": API_KEY,
                        "Content-Type": "application/json"
                    }
                )
                
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    reply = result['reply']
                    print(f"Agent: {reply}")
                    print(f"Response length: {len(reply)} characters")
                    print(f"⏱️  Actual delay: {elapsed:.2f}s")
                    
                    # Calculate what the delay should have been
                    expected_base = len(reply) / 50
                    expected_min = max(2.0, expected_base - 0.5)
                    expected_max = min(8.0, expected_base + 0.5)
                    print(f"✓ Expected range: {expected_min:.2f}s - {expected_max:.2f}s")
                    
                    if expected_min <= elapsed <= expected_max + 0.5:  # +0.5 for processing time
                        print("✅ Delay is within expected range!")
                    else:
                        print("⚠️  Delay outside expected range (may include processing time)")
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
                
            except Exception as e:
                print(f"❌ Request failed: {e}")
            
            await asyncio.sleep(1)  # Small pause between tests
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    print("\n🚀 Starting Typing Delay Test...\n")
    asyncio.run(test_delay())
