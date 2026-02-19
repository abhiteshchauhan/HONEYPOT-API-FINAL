"""
In-memory session management (fallback when Redis is unavailable)
"""
import time
from typing import Optional, Dict
from app.models import SessionData, Message, ExtractedIntelligence, EngagementMetrics


class InMemorySessionManager:
    """Manage conversation sessions using in-memory dict"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
    
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
            engagementMetrics=EngagementMetrics(),
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
        """Update session with new message and data"""
        session = await self.get_session(session_id)
        if not session:
            session = await self.create_session(session_id)
        
        session.conversationHistory.append(new_message)
        session.messageCount = len(session.conversationHistory)
        
        if scam_detected:
            session.scamDetected = True
        
        if intelligence:
            session.extractedIntelligence = intelligence
        
        # Update notes with smart summarization (keep under 100 words)
        if notes:
            if session.agentNotes:
                # Combine old and new notes
                combined = f"{session.agentNotes} | {notes}"
                # Keep only unique tactics/behaviors
                parts = [p.strip() for p in combined.split('|')]
                unique_parts = []
                seen = set()
                for part in parts:
                    if part and part not in seen:
                        unique_parts.append(part)
                        seen.add(part)
                # Limit to last 8 unique observations to stay under 100 words
                session.agentNotes = " | ".join(unique_parts[-8:])
            else:
                session.agentNotes = notes
        
        await self.save_session(session)
        return session
    
    async def mark_callback_sent(self, session_id: str) -> None:
        """Mark that final callback has been sent"""
        session = await self.get_session(session_id)
        if session:
            session.callbackSent = True
            await self.save_session(session)
    
    async def get_message_count(self, session_id: str) -> int:
        """Get total message count for session"""
        session = await self.get_session(session_id)
        return session.messageCount if session else 0
    
    async def should_send_callback(self, session_id: str) -> bool:
        """Check if final callback should be sent"""
        from app.config import config
        
        session = await self.get_session(session_id)
        
        if not session or session.callbackSent or not session.scamDetected:
            return False
        
        if session.messageCount >= config.MIN_MESSAGES_FOR_CALLBACK:
            return True
        
        total_intelligence = (
            len(session.extractedIntelligence.bankAccounts) +
            len(session.extractedIntelligence.upiIds) +
            len(session.extractedIntelligence.phoneNumbers) +
            len(session.extractedIntelligence.phishingLinks)
        )
        
        if total_intelligence >= config.MIN_INTELLIGENCE_ITEMS:
            return True
        
        return False
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session from memory"""
        if session_id in self.sessions:
            del self.sessions[session_id]


# Global session manager instance (in-memory fallback)
inmemory_session_manager = InMemorySessionManager()
