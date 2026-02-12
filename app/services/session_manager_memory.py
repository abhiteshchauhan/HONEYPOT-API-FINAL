"""
In-memory session management (fallback when Redis is unavailable)
Optimized for accurate message counting and concurrency safety.
"""
import time
import asyncio
from typing import Optional, Dict
from app.models import SessionData, Message, ExtractedIntelligence


class InMemorySessionManager:
    """Manage conversation sessions using in-memory dict with high-concurrency protection"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        # The lock prevents "race conditions" where two messages arriving 
        # at the same time might overwrite each other's counts.
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
        """Update session with new message and data - Fixes message counting bugs"""
        async with self._lock:
            session = await self.get_session(session_id)
            if not session:
                session = await self.create_session(session_id)
            
            # 1. Append message to the actual list
            session.conversationHistory.append(new_message)
            
            # 2. Fix: Derive count from actual list length to ensure 100% accuracy
            session.messageCount = len(session.conversationHistory)
            
            # 3. Update flags and metadata
            if scam_detected:
                session.scamDetected = True
            
            if intelligence:
                session.extractedIntelligence = intelligence
            
            if notes:
                # Cleanly append notes without extra pipes at the start
                existing_notes = session.agentNotes.strip() if session.agentNotes else ""
                if existing_notes:
                    session.agentNotes = f"{existing_notes} | {notes}"
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
        """Get total message count for session by measuring actual history size"""
        session = await self.get_session(session_id)
        if not session:
            return 0
        return len(session.conversationHistory)
    
    async def should_send_callback(self, session_id: str) -> bool:
        """Check if final callback should be sent using safe attribute access"""
        try:
            from app.config import config
        except ImportError:
            return False
            
        session = await self.get_session(session_id)
        
        if not session or session.callbackSent or not session.scamDetected:
            return False
        
        # Priority 1: Check Message Count
        if session.messageCount >= config.MIN_MESSAGES_FOR_CALLBACK:
            return True
        
        # Priority 2: Check Intelligence Items Safely
        intel = session.extractedIntelligence
        # Using getattr and 'or []' prevents Error 500 if fields are missing or None
        total_intelligence = (
            len(getattr(intel, 'bankAccounts', []) or []) +
            len(getattr(intel, 'upiIds', []) or []) +
            len(getattr(intel, 'phoneNumbers', []) or []) +
            len(getattr(intel, 'phishingLinks', []) or [])
        )
        
        if total_intelligence >= config.MIN_INTELLIGENCE_ITEMS:
            return True
        
        return False
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session from memory safely"""
        async with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]


# Global session manager instance (in-memory fallback)
inmemory_session_manager = InMemorySessionManager()