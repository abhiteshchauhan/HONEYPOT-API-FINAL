"""
Pydantic models for request/response validation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """Individual message structure"""
    sender: str = Field(..., description="Sender of the message: 'scammer' or 'user'")
    text: str = Field(..., description="Message content")
    timestamp: int = Field(..., description="Epoch time in milliseconds")


class Metadata(BaseModel):
    """Optional metadata about the conversation"""
    channel: Optional[str] = Field(None, description="Communication channel: SMS/WhatsApp/Email/Chat")
    language: Optional[str] = Field(None, description="Language used")
    locale: Optional[str] = Field(None, description="Country or region code")


class MessageRequest(BaseModel):
    """Incoming message request from evaluation platform"""
    sessionId: str = Field(..., description="Unique session identifier")
    message: Message = Field(..., description="Current incoming message")
    conversationHistory: List[Message] = Field(default_factory=list, description="Previous messages in conversation")
    metadata: Optional[Metadata] = Field(None, description="Optional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "sessionId": "wertyu-dfghj-ertyui",
                "message": {
                    "sender": "scammer",
                    "text": "Your bank account will be blocked today. Verify immediately.",
                    "timestamp": 1770005528731
                },
                "conversationHistory": [],
                "metadata": {
                    "channel": "SMS",
                    "language": "English",
                    "locale": "IN"
                }
            }
        }


class ExtractedIntelligence(BaseModel):
    """Extracted intelligence from scammer"""
    bankAccounts: List[str] = Field(default_factory=list, description="Extracted bank account numbers")
    upiIds: List[str] = Field(default_factory=list, description="Extracted UPI IDs")
    phishingLinks: List[str] = Field(default_factory=list, description="Extracted URLs/links")
    phoneNumbers: List[str] = Field(default_factory=list, description="Extracted phone numbers")
    suspiciousKeywords: List[str] = Field(default_factory=list, description="Detected scam keywords")


class MessageResponse(BaseModel):
    """Response returned to evaluation platform"""
    status: str = Field(..., description="Response status: 'success' or 'error'")
    reply: str = Field(..., description="Agent's response message")
    scamDetected: bool = Field(..., description="Whether scam was detected")
    totalMessagesExchanged: int = Field(..., description="Total messages in conversation")
    extractedIntelligence: ExtractedIntelligence = Field(..., description="All extracted intelligence")
    agentNotes: str = Field(..., description="Summary of scammer behavior")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "reply": "Why is my account being suspended?",
                "scamDetected": True,
                "totalMessagesExchanged": 5,
                "extractedIntelligence": {
                    "bankAccounts": [],
                    "upiIds": [],
                    "phishingLinks": ["https://sbi.co.in/secure-login"],
                    "phoneNumbers": ["9876543210"],
                    "suspiciousKeywords": ["urgent", "verify", "account", "blocked"]
                },
                "agentNotes": "Used urgency tactics; Banking/financial scam"
            }
        }


class FinalResultPayload(BaseModel):
    """Payload sent to GUVI callback endpoint"""
    sessionId: str = Field(..., description="Session identifier")
    scamDetected: bool = Field(..., description="Whether scam was confirmed")
    totalMessagesExchanged: int = Field(..., description="Total messages in conversation")
    extractedIntelligence: ExtractedIntelligence = Field(..., description="All extracted intelligence")
    agentNotes: str = Field(..., description="Summary of scammer behavior")

    class Config:
        json_schema_extra = {
            "example": {
                "sessionId": "abc123-session-id",
                "scamDetected": True,
                "totalMessagesExchanged": 18,
                "extractedIntelligence": {
                    "bankAccounts": ["XXXX-XXXX-XXXX"],
                    "upiIds": ["scammer@upi"],
                    "phishingLinks": ["http://malicious-link.example"],
                    "phoneNumbers": ["+91XXXXXXXXXX"],
                    "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
                },
                "agentNotes": "Scammer used urgency tactics and payment redirection"
            }
        }


class ScamDetectionResult(BaseModel):
    """Internal scam detection result"""
    is_scam: bool = Field(..., description="Whether message is likely a scam")
    confidence: float = Field(..., description="Confidence score 0-1")
    categories: List[str] = Field(default_factory=list, description="Detected scam categories")
    reasoning: Optional[str] = Field(None, description="Detection reasoning")


class SessionData(BaseModel):
    """Session data stored in Redis"""
    sessionId: str
    conversationHistory: List[Message] = Field(default_factory=list)
    messageCount: int = Field(default=0)
    scamDetected: bool = Field(default=False)
    extractedIntelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    agentNotes: str = Field(default="")
    callbackSent: bool = Field(default=False)
    createdAt: Optional[int] = Field(default=None)
    updatedAt: Optional[int] = Field(default=None)
