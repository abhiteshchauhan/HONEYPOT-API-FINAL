"""
In-memory session management (fallback when Redis is unavailable)
Optimized for thread-safe message counting and persistence across requests.
"""
import time
import asyncio
from typing import Optional, Dict
from app.models import SessionData, Message, ExtractedIntelligence

# This helps you verify if your server is restarting unexpectedly
print("--- [SYSTEM] SESSION MANAGER MODULE LOADED ---")

class InMemorySessionManager:
    """Manage conversation sessions using in-memory dict with state protection"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        # The lock ensures that rapid messages don't interfere with each other
        self._lock: Optional[asyncio.Lock] = None
        # Track the instance ID to ensure you aren't creating new managers accidentally
        self._instance_id = id(self)
        print(f"--- [DEBUG] INITIALIZED MANAGER INSTANCE: {self._instance_id} ---")
    
    def _get_lock(self) -> asyncio.Lock:
        """Safe lock initialization for FastAPI/Asyncio loops"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock
    
    async def connect(self):
        pass
    
    async def disconnect(self):
        pass
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve session data from memory"""
        return self.sessions.get(session_id)
    
    async def create_session(self, session_id: str) -> SessionData:
        """Create a new session object"""
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
        """Persist session data to the dictionary"""
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
        """Atomically update session and increment message count"""
        async with self._get_lock():
            session = self.sessions.get(session_id)
            
            if not session:
                print(f"--- [DEBUG] New Session Created: {session_id} ---")
                session = await self.create_session(session_id)
            else:
                print(f"--- [DEBUG] Updating Existing Session: {session_id} (Current Messages: {session.messageCount}) ---")
            
            # 1. ADD MESSAGE TO LIST
            session.conversationHistory.append(new_message)
            
            # 2. SOURCE OF TRUTH: Count the actual history list
            session.messageCount = len(session.conversationHistory)
            
            # 3. UPDATE METADATA
            if scam_detected:
                session.scamDetected = True
            
            if intelligence:
                session.extractedIntelligence = intelligence
            
            if notes:
                clean_notes = session.agentNotes.strip() if session.agentNotes else ""
                if clean_notes:
                    session.agentNotes = f"{clean_notes} | {notes}"
                else:
                    session.agentNotes = notes
            
            # 4. SAVE BACK TO DICTIONARY
            await self.save_session(session)
            
            print(f"--- [DEBUG] SUCCESS: Session {session_id} now has {session.messageCount} messages. ---")
            return session
    
    async def get_message_count(self, session_id: str) -> int:
        """Get reliable count from history length"""
        session = self.sessions.get(session_id)
        if not session:
            return 0
        return len(session.conversationHistory)
    
    async def should_send_callback(self, session_id: str) -> bool:
        """Check thresholds using safe attribute checks to prevent Error 500"""
        try:
            from app.config import config
        except ImportError:
            return False
            
        session = self.sessions.get(session_id)
        if not session or session.callbackSent or not session.scamDetected:
            return False
        
        # Priority 1: Message Threshold
        if len(session.conversationHistory) >= config.MIN_MESSAGES_FOR_CALLBACK:
            return True
        
        # Priority 2: Intelligence Threshold
        intel = session.extractedIntelligence
        # getattr handles missing fields; 'or []' handles None values
        total_intel = (
            len(getattr(intel, 'bankAccounts', []) or []) +
            len(getattr(intel, 'upiIds', []) or []) +
            len(getattr(intel, 'phoneNumbers', []) or []) +
            len(getattr(intel, 'phishingLinks', []) or [])
        )
        
        return total_intel >= config.MIN_INTELLIGENCE_ITEMS
    
    async def delete_session(self, session_id: str) -> None:
        """Remove session from memory"""
        async with self._get_lock():
            self.sessions.pop(session_id, None)


# --- CRITICAL: Use this global instance in your routes ---
inmemory_session_manager = InMemorySessionManager()