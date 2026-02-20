"""
Main FastAPI application - Agentic Honey-Pot API
"""
import time
import random
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import MessageRequest, MessageResponse, Message
from app.auth import verify_api_key
from app.config import config
from app.services.scam_detector import ScamDetector
from app.services.ai_agent import AIAgent
from app.services.intelligence import IntelligenceExtractor
from app.services.session_manager import session_manager
from app.services.session_manager_memory import inmemory_session_manager
from app.services.callback import callback_service

# Global variable to track which session manager to use
active_session_manager = None
use_redis = True


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan (startup/shutdown events)
    """
    # Startup
    global active_session_manager, use_redis
    print("[STARTUP] Starting Agentic Honey-Pot API...")
    
    # Validate configuration
    try:
        config.validate()
        print("[OK] Configuration validated")
    except ValueError as e:
        print(f"[ERROR] Configuration error: {e}")
        raise
    
    # Test Redis connection
    try:
        await session_manager.connect()
        print("[OK] Redis connection established")
        active_session_manager = session_manager
        use_redis = True
    except Exception as e:
        print(f"[WARNING] Redis connection failed: {e}")
        print("  Falling back to in-memory session storage")
        active_session_manager = inmemory_session_manager
        use_redis = False
    
    print(f"[OK] API ready at /chat endpoint")
    print(f"  Model: {config.OPENAI_MODEL}")
    print(f"  Min messages for callback: {config.MIN_MESSAGES_FOR_CALLBACK}")
    
    yield
    
    # Shutdown
    print("[SHUTDOWN] Shutting down...")
    await session_manager.disconnect()
    print("[OK] Cleanup completed")


# Initialize FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="AI-powered agentic honeypot for detecting and engaging scammers",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize services (lazy initialization)
scam_detector: ScamDetector = None
ai_agent: AIAgent = None


def get_scam_detector() -> ScamDetector:
    """Get or create ScamDetector instance"""
    global scam_detector
    if scam_detector is None:
        scam_detector = ScamDetector()
    return scam_detector


def get_ai_agent() -> AIAgent:
    """Get or create AIAgent instance"""
    global ai_agent
    if ai_agent is None:
        ai_agent = AIAgent()
    return ai_agent


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "status": "operational",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET)",
            "results": "/results/{sessionId} (GET)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Test Redis connection
    redis_ok = False
    try:
        await session_manager.connect()
        redis_ok = True
    except Exception as e:
        print(f"Redis health check failed: {e}")
    
    return {
        "status": "healthy" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": int(time.time() * 1000)
    }


@app.get("/results/{session_id}")
async def get_final_results(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get the final result payload for a specific session
    
    This endpoint returns the complete intelligence and conversation data
    for a given session in the same format as the callback payload.
    """
    try:
        # Get session data
        session = await active_session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        from app.models import FinalResultPayload
        payload = FinalResultPayload(
            sessionId=session.sessionId,
            scamDetected=session.scamDetected,
            scamType=session.scamType,
            scamCategories=session.scamCategories,
            confidenceScore=session.confidenceScore,
            extractedIntelligence=session.extractedIntelligence,
            agentNotes=session.agentNotes or "Session data retrieved",
            engagementMetrics={
                "totalMessagesExchanged": session.messageCount,
                "engagementDurationSeconds": session.engagementMetrics.engagementDurationSeconds
            }
        )
    
        result = {"status": "success"}
        result.update(payload.model_dump())
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving results for session {session_id}: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session results: {str(e)}"
        )

@app.get("/sessions")
async def list_sessions(
    api_key: str = Depends(verify_api_key)
):
    """
    List all active sessions with basic stats
    """
    try:
        if use_redis:
            await session_manager.connect()
            keys = await session_manager.redis.keys("session:*")
            sessions_info = []
            for key in keys:
                session_id = key.replace("session:", "")
                session = await active_session_manager.get_session(session_id)
                if session:
                    sessions_info.append({
                        "sessionId": session.sessionId,
                        "messageCount": session.messageCount,
                        "scamDetected": session.scamDetected,
                        "scamCategories": session.scamCategories,
                        "callbackSent": session.callbackSent,
                        "createdAt": session.createdAt,
                        "updatedAt": session.updatedAt
                    })
        else:
            sessions_info = [
                {
                    "sessionId": s.sessionId,
                    "messageCount": s.messageCount,
                    "scamDetected": s.scamDetected,
                    "scamCategories": s.scamCategories,
                    "callbackSent": s.callbackSent,
                    "createdAt": s.createdAt,
                    "updatedAt": s.updatedAt
                }
                for s in inmemory_session_manager.sessions.values()
            ]
        
        return {
            "status": "success",
            "totalSessions": len(sessions_info),
            "sessions": sessions_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing sessions: {str(e)}"
        )


@app.post("/chat", response_model=MessageResponse)
async def chat(
    request: MessageRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Main chat endpoint for receiving and responding to messages
    
    This endpoint:
    1. Receives a message from the evaluation platform
    2. Detects if it's a scam
    3. Engages the AI agent if scam detected
    4. Extracts intelligence
    5. Returns a human-like response
    6. Triggers callback when appropriate
    """
    try:
        # Get services
        detector = get_scam_detector()
        agent = get_ai_agent()
        
        # Get or create session
        session = await active_session_manager.get_session(request.sessionId)
        

        if not session:
            session = await active_session_manager.create_session(request.sessionId)
            # Option E: Initialize with client's conversation history on first message
            if request.conversationHistory:
                session.conversationHistory = list(request.conversationHistory)
                session.messageCount = len(session.conversationHistory)
                await active_session_manager.save_session(session)
        
        # Detect scam
        detection_result = await detector.detect_scam(
            request.message,
            request.conversationHistory
        )
        
        print(f"Session {request.sessionId}: Scam detection - "
              f"{'SCAM' if detection_result.is_scam else 'NOT SCAM'} "
              f"(confidence: {detection_result.confidence:.2f})")
        
        # Extract intelligence from current message
        extractor = IntelligenceExtractor()
        extractor.extract_from_text(request.message.text)
        
        # Also extract from conversation history if this is first message
        if not session.conversationHistory:
            extractor.extract_from_messages(request.conversationHistory)
        
        # Merge with existing intelligence from session
        if session.extractedIntelligence:
            extractor.merge_intelligence(session.extractedIntelligence)
        
        intelligence = extractor.get_extracted_intelligence()
        
        # Generate response based on scam detection
        if detection_result.is_scam:
            # Scam detected - engage AI agent
            response_text, agent_notes = await agent.generate_context_aware_response(
                request.message,
                request.conversationHistory,
                detection_result.categories
            )
            
            # Use concise agent notes only
            notes = agent_notes
        else:
            # Not a scam - give neutral response
            response_text = "I'm not sure what this is about. Can you clarify?"
            notes = "No scam detected"
        
        # Create user response message for history
        user_response = Message(
            sender="user",
            text=response_text,
            timestamp=int(time.time() * 1000)
        )
        
        # Resolve human-readable scam type from categories
        resolved_scam_type = ScamDetector.resolve_scam_type(detection_result.categories) if detection_result.is_scam else "Unknown"
        
        # Update session
        session = await active_session_manager.update_session(
            session_id=request.sessionId,
            new_message=request.message,
            scam_detected=detection_result.is_scam,
            intelligence=intelligence,
            notes=notes,
            categories=detection_result.categories if detection_result.is_scam else [],
            confidence=detection_result.confidence if detection_result.is_scam else 0.0,
            scam_type=resolved_scam_type
        )
        
        # Add user's response to session too
        session.conversationHistory.append(user_response)
        session.messageCount = len(session.conversationHistory)
        
        # Calculate engagement duration using session creation time vs now
        try:
            now_ms = int(time.time() * 1000)
            start_ms = session.createdAt or now_ms
            duration_seconds = max(0, (now_ms - start_ms) // 1000)
            # Ensure at least messageCount * 3 seconds as a floor (realistic minimum)
            session.engagementMetrics.engagementDurationSeconds = max(duration_seconds, session.messageCount * 3)
        except Exception as e:
            print(f"Error calculating duration: {e}")
        
        await active_session_manager.save_session(session)
        
        # Check if we should send callback
        if detection_result.is_scam:
            # Get fresh session with updated message count
            updated_session = await active_session_manager.get_session(request.sessionId)
            should_callback = await active_session_manager.should_send_callback(request.sessionId)
            
            if should_callback:
                print(f"Session {request.sessionId}: Triggering callback (messages: {updated_session.messageCount})")
                
                # Send callback with updated session that includes agent response
                callback_result = await callback_service.send_if_criteria_met(updated_session)
                
                if callback_result:
                    await active_session_manager.mark_callback_sent(request.sessionId)
                    print(f"[OK] Callback sent for session {request.sessionId}")
                elif callback_result is False:
                    print(f"[ERROR] Callback failed for session {request.sessionId}")
        
        # Log intelligence status
        if intelligence:
            print(f"Session {request.sessionId}: {extractor.get_intelligence_summary()}")
        
        # Calculate realistic typing delay based on response length
        # typing_speed = 50  # characters per second
        # base_delay = len(response_text) / typing_speed
        # jitter = random.uniform(-0.5, 0.5)
        # delay = max(2.0, min(5.0, base_delay + jitter))
        
        # print(f"Session {request.sessionId}: Simulating typing delay of {delay:.2f}s for {len(response_text)} chars")
        # await asyncio.sleep(delay)
        
        # Return response with full session intelligence
        return MessageResponse(
            status="success",
            reply=response_text,
            sessionId=request.sessionId,
            scamDetected=session.scamDetected,
            scamType=session.scamType,
            scamCategories=session.scamCategories,
            confidenceScore=session.confidenceScore,
            extractedIntelligence=session.extractedIntelligence.model_dump(),
            agentNotes=session.agentNotes or None,
            engagementMetrics={
                "totalMessagesExchanged": session.messageCount,
                "engagementDurationSeconds": session.engagementMetrics.engagementDurationSeconds
            }
        )
    
    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    print(f"Unhandled exception: {exc}")
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "Internal server error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG
    )
