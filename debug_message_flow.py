"""
Debug script to trace message flow and identify why count is 16 instead of 20
"""
import asyncio
import httpx
import time

API_URL = "http://localhost:8000"
API_KEY = "honeypot-api-key-2024-secure"

async def debug_message_flow():
    """Send messages and track the count at each step"""
    
    session_id = f"debug-flow-{int(time.time())}"
    
    print("=" * 80)
    print("MESSAGE FLOW DEBUG - Tracking Count at Each Step")
    print("=" * 80)
    print(f"Session ID: {session_id}\n")
    
    # Track conversation history on client side (like the real client would)
    client_conversation_history = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Send 10 scammer messages
        for i in range(1, 11):
            scammer_text = f"Message {i}: Call 9876543210 to verify your account urgently!"
            
            print(f"\n{'='*80}")
            print(f"SENDING MESSAGE {i}")
            print(f"{'='*80}")
            print(f"Scammer: {scammer_text}")
            print(f"Client's conversation history length: {len(client_conversation_history)}")
            
            # Create scammer message
            scammer_msg = {
                "sender": "scammer",
                "text": scammer_text,
                "timestamp": int(time.time() * 1000)
            }
            
            payload = {
                "sessionId": session_id,
                "message": scammer_msg,
                "conversationHistory": client_conversation_history.copy()
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
                    
                    print(f"Agent: {agent_reply[:60]}...")
                    
                    # Update client's conversation history (like real client would)
                    client_conversation_history.append(scammer_msg)
                    client_conversation_history.append({
                        "sender": "user",
                        "text": agent_reply,
                        "timestamp": int(time.time() * 1000) + 1
                    })
                    
                    print(f"\nClient tracking:")
                    print(f"  - Client conversation history: {len(client_conversation_history)} messages")
                    print(f"  - Expected server count: {len(client_conversation_history)}")
                    
                    # Check server's count
                    results_response = await client.get(
                        f"{API_URL}/results/{session_id}",
                        headers={"X-API-Key": API_KEY}
                    )
                    
                    if results_response.status_code == 200:
                        server_data = results_response.json()
                        server_history_len = len(server_data['conversationHistory'])
                        server_count = server_data['data']['totalMessagesExchanged']
                        
                        print(f"\nServer tracking:")
                        print(f"  - Server conversationHistory: {server_history_len} messages")
                        print(f"  - Server messageCount: {server_count}")
                        
                        if server_count != len(client_conversation_history):
                            print(f"\n⚠️  MISMATCH DETECTED!")
                            print(f"  - Client expects: {len(client_conversation_history)}")
                            print(f"  - Server reports: {server_count}")
                            print(f"  - Difference: {len(client_conversation_history) - server_count} messages missing")
                        else:
                            print(f"\n✅ Counts match!")
                    
                else:
                    print(f"❌ Error: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")
                break
            
            await asyncio.sleep(0.5)
        
        # Final check
        print(f"\n{'='*80}")
        print("FINAL RESULTS")
        print(f"{'='*80}")
        
        try:
            final_response = await client.get(
                f"{API_URL}/results/{session_id}",
                headers={"X-API-Key": API_KEY}
            )
            
            if final_response.status_code == 200:
                final_data = final_response.json()
                server_history = final_data['conversationHistory']
                server_count = final_data['data']['totalMessagesExchanged']
                
                print(f"\nClient side:")
                print(f"  Total messages tracked: {len(client_conversation_history)}")
                print(f"  Scammer messages: 10")
                print(f"  Agent responses: 10")
                
                print(f"\nServer side:")
                print(f"  conversationHistory length: {len(server_history)}")
                print(f"  totalMessagesExchanged: {server_count}")
                
                print(f"\nAnalysis:")
                if server_count == len(client_conversation_history):
                    print(f"  ✅ SUCCESS: Counts match ({server_count})")
                else:
                    print(f"  ❌ FAILURE: Count mismatch")
                    print(f"     Expected: {len(client_conversation_history)}")
                    print(f"     Got: {server_count}")
                    print(f"     Missing: {len(client_conversation_history) - server_count} messages")
                    
                    # Analyze which messages are in server history
                    print(f"\n  Server conversation history breakdown:")
                    scammer_count = sum(1 for msg in server_history if msg['sender'] == 'scammer')
                    agent_count = sum(1 for msg in server_history if msg['sender'] == 'user')
                    print(f"     Scammer messages: {scammer_count}")
                    print(f"     Agent messages: {agent_count}")
                    print(f"     Total: {scammer_count + agent_count}")
                
        except Exception as e:
            print(f"❌ Failed to get final results: {e}")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    print("\n🔍 Starting Message Flow Debug...\n")
    asyncio.run(debug_message_flow())
