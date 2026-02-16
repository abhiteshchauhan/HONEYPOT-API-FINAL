"""
Test message counting to verify all messages are counted correctly
"""
import asyncio
import httpx
import time

API_URL = "http://localhost:8000"
API_KEY = "honeypot-api-key-2024-secure"

async def test_message_counting():
    """Test that totalMessagesExchanged counts all messages (scammer + agent)"""
    
    session_id = f"message-count-test-{int(time.time())}"
    
    print("=" * 70)
    print("MESSAGE COUNTING TEST")
    print("=" * 70)
    print(f"Session ID: {session_id}\n")
    print("Testing that totalMessagesExchanged includes both scammer and agent messages\n")
    
    scammer_messages = [
        "Your bank account will be blocked. Call 9876543210 immediately.",
        "Transfer ₹500 to verify your account at fraud@paytm",
        "Send payment to account 123456789012345 now!"
    ]
    
    conversation_history = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, scammer_text in enumerate(scammer_messages, 1):
            print(f"\n--- Message Pair {i} ---")
            print(f"Scammer: {scammer_text[:60]}{'...' if len(scammer_text) > 60 else ''}")
            
            payload = {
                "sessionId": session_id,
                "message": {
                    "sender": "scammer",
                    "text": scammer_text,
                    "timestamp": int(time.time() * 1000)
                },
                "conversationHistory": conversation_history
            }
            
            try:
                response = await client.post(
                    f"{API_URL}/chat",
                    json=payload,
                    headers={
                        "X-API-Key": API_KEY,
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    agent_reply = result['reply']
                    print(f"Agent: {agent_reply}")
                    
                    # Update conversation history
                    conversation_history.append({
                        "sender": "scammer",
                        "text": scammer_text,
                        "timestamp": int(time.time() * 1000)
                    })
                    conversation_history.append({
                        "sender": "user",
                        "text": agent_reply,
                        "timestamp": int(time.time() * 1000) + 1
                    })
                    
                    expected_count = len(conversation_history)
                    print(f"Expected message count: {expected_count} (scammer: {i}, agent: {i})")
                    
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
                    break
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")
                break
            
            await asyncio.sleep(1)
        
        # Get final results to check totalMessagesExchanged
        print("\n" + "=" * 70)
        print("CHECKING FINAL RESULTS")
        print("=" * 70)
        
        try:
            results_response = await client.get(
                f"{API_URL}/results/{session_id}",
                headers={"X-API-Key": API_KEY}
            )
            
            if results_response.status_code == 200:
                final_results = results_response.json()
                data = final_results['data']
                
                total_messages = data['totalMessagesExchanged']
                expected_total = len(conversation_history)
                
                print(f"\n📊 Final Results:")
                print(f"  Total Messages Exchanged: {total_messages}")
                print(f"  Expected Total: {expected_total}")
                print(f"  Scammer Messages: {len(scammer_messages)}")
                print(f"  Agent Responses: {len(scammer_messages)}")
                
                if total_messages == expected_total:
                    print(f"\n✅ SUCCESS: Message counting is correct!")
                    print(f"   All {total_messages} messages (scammer + agent) are counted.")
                else:
                    print(f"\n❌ FAILURE: Message count mismatch!")
                    print(f"   Expected: {expected_total}, Got: {total_messages}")
                
                # Show extracted intelligence
                intel = data['extractedIntelligence']
                print(f"\n🔍 Extracted Intelligence:")
                if intel['phoneNumbers']:
                    print(f"  📱 Phone Numbers: {intel['phoneNumbers']}")
                if intel['upiIds']:
                    print(f"  💳 UPI IDs: {intel['upiIds']}")
                if intel['bankAccounts']:
                    print(f"  🏦 Bank Accounts: {intel['bankAccounts']}")
                
                print(f"\n📝 Agent Notes: {data['agentNotes']}")
                print(f"🔔 Callback Sent: {final_results['callbackSent']}")
                
            else:
                print(f"❌ Error retrieving results: {results_response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed to retrieve results: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    print("\n🚀 Starting Message Counting Test...\n")
    asyncio.run(test_message_counting())
