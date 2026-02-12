"""
In-memory session management (fallback when Redis is unavailable)
Optimized for thread-safety and accurate message counting.
"""
import time
import asyncio
from typing import Optional, Dict
from app.models import SessionData, Message, ExtractedIntelligence


class InMemorySessionManager:
    """Manage conversation sessions using in-memory dict with concurrency protection"""
    
    def _init_(self):
        self.sessions: Dict[str, SessionData] = {}
        # The lock ensures that even if 100 messages arrive at once, 
        # they are processed one-by-one to keep the count 100% accurate.
        self._lock = asyncio.Lock()
    
    async def connect(self):
        """Initialize (no-op for in-memory)"""
        pass
    
    async def disconnect(self):
        """Close (no-op for in-memory)"""
        pass
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve session data from memory"""
        return self.sessions.get(session_id)
    
    async def create_session(self, session_id: str) -> SessionData:
        """Create a new session"""
        now = int(time.time() * 1000)
        
        session = SessionData(
            sessionId=session_id,
            conversationHistory=[],
            messageCount=0,
            scamDetected=False,
            extractedIntelligence=ExtractedIntelligence(),
            agentNotes="",
            callbackSent=False,
            createdAt=now,
            updatedAt=now
        )
        
        self.sessions[session_id] = session
        return session
    
    async def save_session(self, session: SessionData) -> None:
        """Save session data to memory"""
        session.updatedAt = int(time.time() * 1000)
        self.sessions[session.sessionId] = session
    
    async def update_session(
        self,
        session_id: str,
        new_message: Message,
        scam_detected: bool = False,
        intelligence: Optional[ExtractedIntelligence] = None,
        notes: str = ""
    ) -> SessionData:
        """Update session with new message and data using atomicity"""
        async with self._lock:
            session = await self.get_session(session_id)
            if not session:
                session = await self.create_session(session_id)
            
            # 1. Update History
            session.conversationHistory.append(new_message)
            
            # 2. Fix: Always derive count from the actual list length
            session.messageCount = len(session.conversationHistory)
            
            # 3. Update Metadata
            if scam_detected:
                session.scamDetected = True
            
            if intelligence:
                session.extractedIntelligence = intelligence
            
            if notes:
                # Cleanly append notes without leading separators
                if session.agentNotes:
                    session.agentNotes += f" | {notes}"
                else:
                    session.agentNotes = notes
            
            await self.save_session(session)
            return session
    
    async def mark_callback_sent(self, session_id: str) -> None:
        """Mark that final callback has been sent"""
        async with self._lock:
            session = await self.get_session(session_id)
            if session:
                session.callbackSent = True
                await self.save_session(session)
    
    async def get_message_count(self, session_id: str) -> int:
        """Get total message count for session reliably"""
        session = await self.get_session(session_id)
        if not session:
            return 0
        # Return the actual length of history to ensure accuracy
        return len(session.conversationHistory)
    
    async def should_send_callback(self, session_id: str) -> bool:
        """Check if final callback should be sent"""
        from app.config import config
        
        session = await self.get_session(session_id)
        
        if not session or session.callbackSent or not session.scamDetected:
            return False
        
        # Priority 1: Message Count Threshold
        if session.messageCount >= config.MIN_MESSAGES_FOR_CALLBACK:
            return True
        
        # Priority 2: Intelligence Threshold
        intel = session.extractedIntelligence
        total_intelligence = (
            len(intel.bankAccounts or []) +
            len(intel.upiIds or []) +
            len(intel.phoneNumbers or []) +
            len(intel.phishingLinks or [])
        )
        
        if total_intelligence >= config.MIN_INTELLIGENCE_ITEMS:
            return True
        
        return False
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session from memory"""
        async with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]


# Global session manager instance (in-memory fallback)
inmemory_session_manager = InMemorySessionManager()