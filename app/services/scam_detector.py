"""
Scam detection service using pattern matching and LLM analysis
"""
import re
import json
from typing import List
from openai import AsyncOpenAI
from app.models import Message, ScamDetectionResult
from app.config import config
from app.prompts.agent_system import get_scam_detection_prompt


class ScamDetector:
    """Detect scam intent using pattern matching and LLM analysis"""
    
    # Phase 1: Pattern-based detection keywords
    URGENCY_KEYWORDS = {
        "urgent", "immediately", "now", "today", "asap", "hurry", 
        "quick", "fast", "expire", "last chance", "limited time"
    }
    
    BANKING_KEYWORDS = {
        "bank", "account", "upi", "payment", "transfer", "otp", 
        "cvv", "pin", "atm", "card", "debit", "credit", "netbanking"
    }
    
    THREAT_KEYWORDS = {
        "blocked", "suspended", "locked", "frozen", "deactivated",
        "legal action", "police", "arrest", "fine", "penalty", "court"
    }
    
    VERIFICATION_KEYWORDS = {
        "verify", "confirm", "authenticate", "validate", "update details",
        "kyc", "click here", "link", "portal"
    }
    
    REWARD_KEYWORDS = {
        "won", "winner", "prize", "lottery", "reward", "cashback",
        "refund", "congratulations", "selected"
    }
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    
    def _pattern_based_detection(self, text: str) -> tuple[bool, float, List[str]]:
        """
        Phase 1: Fast pattern-based detection
        
        Args:
            text: Message text to analyze
            
        Returns:
            Tuple of (is_suspicious, confidence, matched_categories)
        """
        text_lower = text.lower()
        score = 0.0
        categories = []
        
        # Check for urgency
        urgency_matches = sum(1 for keyword in self.URGENCY_KEYWORDS if keyword in text_lower)
        if urgency_matches > 0:
            score += 0.2 * min(urgency_matches, 2)
            categories.append("urgency")
        
        # Check for banking terms
        banking_matches = sum(1 for keyword in self.BANKING_KEYWORDS if keyword in text_lower)
        if banking_matches > 0:
            score += 0.15 * min(banking_matches, 2)
            categories.append("banking")
        
        # Check for threats
        threat_matches = sum(1 for keyword in self.THREAT_KEYWORDS if keyword in text_lower)
        if threat_matches > 0:
            score += 0.25 * min(threat_matches, 2)
            categories.append("threat")
        
        # Check for verification requests
        verification_matches = sum(1 for keyword in self.VERIFICATION_KEYWORDS if keyword in text_lower)
        if verification_matches > 0:
            score += 0.2 * min(verification_matches, 2)
            categories.append("verification")
        
        # Check for rewards
        reward_matches = sum(1 for keyword in self.REWARD_KEYWORDS if keyword in text_lower)
        if reward_matches > 0:
            score += 0.2 * min(reward_matches, 2)
            categories.append("reward")
        
        # Check for URLs (potential phishing)
        if re.search(r'https?://|www\.', text_lower):
            score += 0.15
            categories.append("phishing_link")
        
        # Check for requests for sensitive info
        sensitive_patterns = [
            r'\b(otp|cvv|pin|password)\b',
            r'\bshare.*\b(account|number|details)\b',
            r'\bsend.*\b(upi|payment)\b'
        ]
        for pattern in sensitive_patterns:
            if re.search(pattern, text_lower):
                score += 0.2
                categories.append("sensitive_info_request")
                break
        
        # Cap score at 1.0
        confidence = min(score, 0.95)
        
        # Consider suspicious if score > threshold
        is_suspicious = confidence >= 0.5
        
        return is_suspicious, confidence, categories
    
    async def _llm_based_detection(
        self, 
        message: str, 
        conversation_history: List[Message]
    ) -> ScamDetectionResult:
        """
        Phase 2: LLM-based analysis for more accurate detection
        
        Args:
            message: Current message to analyze
            conversation_history: Previous messages for context
            
        Returns:
            ScamDetectionResult with detailed analysis
        """
        # Build conversation context
        history_text = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                history_lines.append(f"{msg.sender}: {msg.text}")
            history_text = "\n".join(history_lines)
        
        # Get prompt
        prompt = get_scam_detection_prompt(message, history_text)
        
        try:
            response = await self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            
            return ScamDetectionResult(
                is_scam=result_json.get("is_scam", False),
                confidence=result_json.get("confidence", 0.0),
                categories=result_json.get("categories", []),
                reasoning=result_json.get("reasoning", "")
            )
        
        except Exception as e:
            # Fallback to pattern-based result if LLM fails
            print(f"LLM detection failed: {e}")
            is_suspicious, confidence, categories = self._pattern_based_detection(message)
            return ScamDetectionResult(
                is_scam=is_suspicious,
                confidence=confidence,
                categories=categories,
                reasoning="Pattern-based detection (LLM unavailable)"
            )
    
    async def detect_scam(
        self, 
        message: Message, 
        conversation_history: List[Message]
    ) -> ScamDetectionResult:
        """
        Main detection method combining both phases
        
        Args:
            message: Current message to analyze
            conversation_history: Previous messages for context
            
        Returns:
            ScamDetectionResult with detection outcome
        """
        # Phase 1: Pattern-based detection (fast)
        is_suspicious, pattern_confidence, pattern_categories = \
            self._pattern_based_detection(message.text)
        
        # If pattern confidence is very high or very low, we might skip LLM
        if pattern_confidence >= 0.85:
            # Very likely a scam, but still confirm with LLM
            pass
        elif pattern_confidence < 0.3:
            # Very unlikely a scam, return early
            return ScamDetectionResult(
                is_scam=False,
                confidence=pattern_confidence,
                categories=pattern_categories,
                reasoning="Pattern-based analysis shows low scam likelihood"
            )
        
        # Phase 2: LLM-based detection (accurate)
        llm_result = await self._llm_based_detection(message.text, conversation_history)
        
        # Combine results (weighted average, favoring LLM)
        final_confidence = (pattern_confidence * 0.3) + (llm_result.confidence * 0.7)
        final_is_scam = llm_result.is_scam or (final_confidence >= config.SCAM_DETECTION_CONFIDENCE_THRESHOLD)
        
        # Merge categories
        all_categories = list(set(pattern_categories + llm_result.categories))
        
        return ScamDetectionResult(
            is_scam=final_is_scam,
            confidence=final_confidence,
            categories=all_categories,
            reasoning=llm_result.reasoning or f"Combined detection (pattern: {pattern_confidence:.2f}, LLM: {llm_result.confidence:.2f})"
        )
