"""
Callback service for sending final results to GUVI endpoint
"""
import asyncio
import httpx
from typing import Optional
from app.models import FinalResultPayload, SessionData
from app.config import config


class CallbackService:
    """Handle callbacks to GUVI evaluation endpoint"""
    
    def __init__(self):
        self.callback_url = config.GUVI_CALLBACK_URL
        self.timeout = config.CALLBACK_TIMEOUT
        self.max_retries = config.CALLBACK_MAX_RETRIES
    
    async def send_final_result(
        self,
        session: SessionData,
        force: bool = False
    ) -> bool:
        """
        Send final results to GUVI callback endpoint
        
        Args:
            session: SessionData containing all intelligence
            force: Force send even if criteria not met
            
        Returns:
            True if callback successful, False otherwise
        """
        # Don't send if already sent
        if session.callbackSent and not force:
            print(f"Callback already sent for session {session.sessionId}")
            return True
        
        # Build payload
        payload = FinalResultPayload(
            sessionId=session.sessionId,
            scamDetected=session.scamDetected,
            totalMessagesExchanged=session.messageCount,
            extractedIntelligence=session.extractedIntelligence,
            agentNotes=session.agentNotes or "Scam engagement completed"
        )
        
        # Send with retry logic
        return await self._send_with_retry(payload)
    
    async def _send_with_retry(self, payload: FinalResultPayload) -> bool:
        """
        Send payload with exponential backoff retry
        
        Args:
            payload: FinalResultPayload to send
            
        Returns:
            True if successful, False if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                success = await self._send_request(payload)
                if success:
                    print(f"[OK] Callback sent successfully for session {payload.sessionId}")
                    return True
                
                # If not successful, wait before retry
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"Callback failed, retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
            
            except Exception as e:
                print(f"Callback error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
        
        print(f"[ERROR] Callback failed after {self.max_retries} attempts for session {payload.sessionId}")
        return False
    
    async def _send_request(self, payload: FinalResultPayload) -> bool:
        """
        Send single HTTP request to callback endpoint
        
        Args:
            payload: FinalResultPayload to send
            
        Returns:
            True if successful (2xx status), False otherwise
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.callback_url,
                    json=payload.model_dump(),
                    headers={
                        "Content-Type": "application/json"
                    },
                    timeout=self.timeout
                )
                
                # Consider 2xx status codes as success
                if 200 <= response.status_code < 300:
                    return True
                
                print(f"Callback returned status {response.status_code}: {response.text}")
                return False
            
            except httpx.TimeoutException:
                print(f"Callback timeout after {self.timeout}s")
                return False
            
            except httpx.RequestError as e:
                print(f"Callback request error: {e}")
                return False
    
    async def send_if_criteria_met(
        self,
        session: SessionData
    ) -> Optional[bool]:
        """
        Send callback only if criteria are met
        
        Args:
            session: SessionData to evaluate
            
        Returns:
            True if sent successfully, False if sent but failed, None if not sent
        """
        # Check if callback should be sent
        if not session.scamDetected:
            return None
        
        if session.callbackSent:
            return None
        
        # Check minimum messages
        min_messages_met = session.messageCount >= config.MIN_MESSAGES_FOR_CALLBACK
        
        # Check intelligence extracted
        total_intelligence = (
            len(session.extractedIntelligence.bankAccounts) +
            len(session.extractedIntelligence.upiIds) +
            len(session.extractedIntelligence.phoneNumbers) +
            len(session.extractedIntelligence.phishingLinks)
        )
        intelligence_met = total_intelligence >= config.MIN_INTELLIGENCE_ITEMS
        
        # Send if either criterion is met
        if min_messages_met or intelligence_met:
            return await self.send_final_result(session)
        
        return None


# Global callback service instance
callback_service = CallbackService()
