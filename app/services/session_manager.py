"""
Redis-based session management
"""
import json
import time
from typing import Optional
from redis import asyncio as aioredis
from app.models import SessionData, Message, ExtractedIntelligence
from app.config import config


class SessionManager:
    """Manage conversation sessions using Redis"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection"""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                config.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test the connection
            await self.redis.ping()
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    def _get_key(self, session_id: str) -> str:
        """
        Get Redis key for session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Redis key string
        """
        return f"session:{session_id}"
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Retrieve session data from Redis
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionData if exists, None otherwise
        """
        await self.connect()
        
        key = self._get_key(session_id)
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        try:
            session_dict = json.loads(data)
            return SessionData(**session_dict)
        except Exception as e:
            print(f"Error parsing session data: {e}")
            return None
    
    async def create_session(self, session_id: str) -> SessionData:
        """
        Create a new session
        
        Args:
            session_id: Session identifier
            
        Returns:
            New SessionData object
        """
        now = int(time.time() * 1000)  # Milliseconds
        
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
        
        await self.save_session(session)
        return session
    
    async def save_session(self, session: SessionData) -> None:
        """
        Save session data to Redis
        
        Args:
            session: SessionData to save
        """
        await self.connect()
        
        session.updatedAt = int(time.time() * 1000)
        
        key = self._get_key(session.sessionId)
        data = session.model_dump_json()
        
        # Save with TTL
        await self.redis.setex(
            key,
            config.REDIS_SESSION_TTL,
            data
        )
    
    async def update_session(
        self,
        session_id: str,
        new_message: Message,
        scam_detected: bool = False,
        intelligence: Optional[ExtractedIntelligence] = None,
        notes: str = ""
    ) -> SessionData:
        """
        Update session with new message and data
        
        Args:
            session_id: Session identifier
            new_message: New message to add
            scam_detected: Whether scam was detected
            intelligence: Updated extracted intelligence
            notes: Agent notes to append
            
        Returns:
            Updated SessionData
        """
        # Get or create session
        session = await self.get_session(session_id)
        if not session:
            session = await self.create_session(session_id)
        
        # Add new message to history
        session.conversationHistory.append(new_message)
        session.messageCount = len(session.conversationHistory)
        
        # Update scam detection status
        if scam_detected:
            session.scamDetected = True
        
        # Update intelligence if provided
        if intelligence:
            session.extractedIntelligence = intelligence
        
        # Append notes
        if notes:
            if session.agentNotes:
                session.agentNotes += f" | {notes}"
            else:
                session.agentNotes = notes
        
        # Save updated session
        await self.save_session(session)
        
        return session
    
    async def mark_callback_sent(self, session_id: str) -> None:
        """
        Mark that final callback has been sent for this session
        
        Args:
            session_id: Session identifier
        """
        session = await self.get_session(session_id)
        if session:
            session.callbackSent = True
            await self.save_session(session)
    
    async def get_message_count(self, session_id: str) -> int:
        """
        Get total message count for session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Message count
        """
        session = await self.get_session(session_id)
        return session.messageCount if session else 0
    
    async def should_send_callback(self, session_id: str) -> bool:
        """
        Check if final callback should be sent
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if callback should be sent
        """
        session = await self.get_session(session_id)
        
        if not session or session.callbackSent or not session.scamDetected:
            return False
        
        # Check if minimum messages exchanged
        if session.messageCount >= config.MIN_MESSAGES_FOR_CALLBACK:
            return True
        
        # Check if significant intelligence extracted
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
        """
        Delete a session from Redis
        
        Args:
            session_id: Session identifier
        """
        await self.connect()
        key = self._get_key(session_id)
        await self.redis.delete(key)


# Global session manager instance
session_manager = SessionManager()
