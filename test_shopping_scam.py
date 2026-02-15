"""
Test online shopping scam scenario
"""
import asyncio
import httpx
import json
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_URL = "http://localhost:8000"
API_KEY = "honeypot-api-key-2024-secure"

async def test_shopping_scam():
    """Test online shopping scam with phone number extraction"""
    
    session_id = "shopping-scam-test-001"
    
    messages = [
        {
            "sender": "scammer",
            "text": "Congratulations! You've won a brand new iPhone 15 Pro! To claim your prize, contact us immediately at 9876543210 or visit our website.",
            "timestamp": 1770005528731
        },
        {
            "sender": "scammer", 
            "text": "This is a limited time offer! Only 5 winners selected. Call 8765432109 now to verify your details and get free delivery.",
            "timestamp": 1770005538731
        },
        {
            "sender": "scammer",
            "text": "To complete your order, please transfer ₹500 as shipping charges to UPI: winner2024@paytm or account number 12345678901234. Hurry!",
            "timestamp": 1770005548731
        },
        {
            "sender": "scammer",
            "text": "For any queries, WhatsApp us at +919988776655 or email support@fake-deals.com. Click here: http://fake-shopping-deal.com/claim",
            "timestamp": 1770005558731
        },
        {
            "sender": "scammer",
            "text": "Your order will be cancelled if payment not received today! Customer care: 7654321098. Act fast!",
            "timestamp": 1770005568731
        }
    ]
    
    print("=" * 60)
    print("ONLINE SHOPPING SCAM TEST")
    print("=" * 60)
    print(f"Session ID: {session_id}\n")
    
    conversation_history = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, msg in enumerate(messages, 1):
            print(f"\n--- Message {i} ---")
            print(f"Scammer: {msg['text']}")
            
            payload = {
                "sessionId": session_id,
                "message": msg,
                "conversationHistory": conversation_history,
                "metadata": {
                    "channel": "WhatsApp",
                    "language": "English",
                    "locale": "IN"
                }
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
                    print(f"Agent: {result['reply']}")
                    
                    conversation_history.append(msg)
                    conversation_history.append({
                        "sender": "user",
                        "text": result['reply'],
                        "timestamp": msg['timestamp'] + 1000
                    })
                else:
                    print(f"Error: {response.status_code} - {response.text}")
                    break
                
            except Exception as e:
                print(f"Request failed: {e}")
                break
            
            await asyncio.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("RETRIEVING FINAL RESULTS")
        print("=" * 60)
        
        try:
            results_response = await client.get(
                f"{API_URL}/results/{session_id}",
                headers={"X-API-Key": API_KEY}
            )
            
            if results_response.status_code == 200:
                final_results = results_response.json()
                
                print(f"\nStatus: {final_results['status']}")
                print(f"Callback Sent: {final_results['callbackSent']}")
                
                data = final_results['data']
                print(f"\n📊 FINAL PAYLOAD:")
                print(f"  Session ID: {data['sessionId']}")
                print(f"  Scam Detected: {data['scamDetected']}")
                print(f"  Total Messages: {data['totalMessagesExchanged']}")
                
                intel = data['extractedIntelligence']
                print(f"\n🔍 EXTRACTED INTELLIGENCE:")
                
                if intel['phoneNumbers']:
                    print(f"  📱 Phone Numbers ({len(intel['phoneNumbers'])}):")
                    for phone in intel['phoneNumbers']:
                        print(f"     • {phone}")
                        # Verify +91- prefix
                        if phone.startswith('+91-'):
                            print(f"       ✓ Correctly formatted with +91- prefix")
                        else:
                            print(f"       ✗ Missing +91- prefix!")
                
                if intel['upiIds']:
                    print(f"  💳 UPI IDs ({len(intel['upiIds'])}):")
                    for upi in intel['upiIds']:
                        print(f"     • {upi}")
                
                if intel['bankAccounts']:
                    print(f"  🏦 Bank Accounts ({len(intel['bankAccounts'])}):")
                    for acc in intel['bankAccounts']:
                        print(f"     • {acc}")
                
                if intel['phishingLinks']:
                    print(f"  🔗 Phishing Links ({len(intel['phishingLinks'])}):")
                    for link in intel['phishingLinks']:
                        print(f"     • {link}")
                
                if intel['suspiciousKeywords']:
                    print(f"  ⚠️  Suspicious Keywords ({len(intel['suspiciousKeywords'])}):")
                    keywords_str = ", ".join(intel['suspiciousKeywords'][:10])
                    if len(intel['suspiciousKeywords']) > 10:
                        keywords_str += f" ... (+{len(intel['suspiciousKeywords']) - 10} more)"
                    print(f"     {keywords_str}")
                
                print(f"\n📝 Agent Notes:")
                print(f"  {data['agentNotes']}")
                
                print("\n" + "=" * 60)
                print("✅ TEST COMPLETED SUCCESSFULLY")
                print("=" * 60)
                
            else:
                print(f"Error retrieving results: {results_response.status_code}")
                print(results_response.text)
                
        except Exception as e:
            print(f"Failed to retrieve results: {e}")

if __name__ == "__main__":
    print("\n🚀 Starting Online Shopping Scam Test...\n")
    asyncio.run(test_shopping_scam())
