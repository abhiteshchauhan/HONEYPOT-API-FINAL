"""
Main FastAPI application - Agentic Honey-Pot API
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
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

active_session_manager = None
use_redis = True

@asynccontextmanager
async def lifespan(app: FastAPI):
    global active_session_manager, use_redis
    print("[STARTUP] Starting Agentic Honey-Pot API...")
    
    try:
        config.validate()
        print("[OK] Configuration validated")
    except ValueError as e:
        print(f"[ERROR] Configuration error: {e}")
        raise
    
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
    
    print("[SHUTDOWN] Shutting down...")
    await session_manager.disconnect()
    print("[OK] Cleanup completed")

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="AI-powered agentic honeypot for detecting and engaging scammers",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scam_detector: ScamDetector = None
ai_agent: AIAgent = None

def get_scam_detector() -> ScamDetector:
    global scam_detector
    if scam_detector is None:
        scam_detector = ScamDetector()
    return scam_detector

def get_ai_agent() -> AIAgent:
    global ai_agent
    if ai_agent is None:
        ai_agent = AIAgent()
    return ai_agent

async def process_background_callback(session, session_id):
    callback_result = await callback_service.send_if_criteria_met(session)
    if callback_result:
        await active_session_manager.mark_callback_sent(session_id)
        print(f"[OK] Callback sent for session {session_id}")
    elif callback_result is False:
        print(f"[ERROR] Callback failed for session {session_id}")

@app.get("/")
async def root():
    return {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "status": "operational",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET)"
        }
    }

@app.get("/health")
async def health_check():
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

@app.post("/chat", response_model=MessageResponse)
async def chat(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    try:
        detector = get_scam_detector()
        agent = get_ai_agent()
        
        session = await active_session_manager.get_session(request.sessionId)
        if not session:
            session = await active_session_manager.create_session(request.sessionId)
        
        detection_result = await detector.detect_scam(
            request.message,
            request.conversationHistory
        )
        
        print(f"Session {request.sessionId}: Scam detection - "
              f"{'SCAM' if detection_result.is_scam else 'NOT SCAM'} "
              f"(confidence: {detection_result.confidence:.2f})")
        
        extractor = IntelligenceExtractor()
        extractor.extract_from_text(request.message.text)
        
        if not session.conversationHistory:
            extractor.extract_from_messages(request.conversationHistory)
        
        if session.extractedIntelligence:
            extractor.merge_intelligence(session.extractedIntelligence)
        
        intelligence = extractor.get_extracted_intelligence()
        
        if detection_result.is_scam:
            response_text, agent_notes = await agent.generate_context_aware_response(
                request.message,
                request.conversationHistory,
                detection_result.categories
            )
            notes = f"{agent_notes}. {detection_result.reasoning}"
        else:
            response_text = "I'm not sure what this is about. Can you clarify?"
            notes = "No scam detected"
        
        user_response = Message(
            sender="user",
            text=response_text,
            timestamp=int(time.time() * 1000)
        )
        
        session = await active_session_manager.update_session(
            session_id=request.sessionId,
            new_message=request.message,
            scam_detected=detection_result.is_scam,
            intelligence=intelligence,
            notes=notes
        )
        
        session.conversationHistory.append(user_response)
        await active_session_manager.save_session(session)
        
        if detection_result.is_scam:
            should_callback = await active_session_manager.should_send_callback(request.sessionId)
            
            if should_callback:
                print(f"Session {request.sessionId}: Triggering callback (messages: {session.messageCount})")
                background_tasks.add_task(process_background_callback, session, request.sessionId)
        
        if intelligence:
            print(f"Session {request.sessionId}: {extractor.get_intelligence_summary()}")
        
        return MessageResponse(
            status="success",
            reply=response_text,
            message_count=session.messageCount
        )
    
    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
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