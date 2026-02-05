"""
OpenAI-powered conversational AI agent
"""
from typing import List
from openai import AsyncOpenAI
from app.models import Message
from app.config import config
from app.prompts.agent_system import get_agent_prompt


class AIAgent:
    """AI Agent for engaging with scammers"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    
    def _build_conversation_context(self, messages: List[Message]) -> str:
        """
        Build conversation context string from message history
        
        Args:
            messages: List of messages in conversation
            
        Returns:
            Formatted conversation string
        """
        if not messages:
            return "This is the first message."
        
        context_lines = []
        for msg in messages:
            role = "Scammer" if msg.sender == "scammer" else "You"
            context_lines.append(f"{role}: {msg.text}")
        
        return "\n".join(context_lines)
    
    async def generate_response(
        self,
        current_message: Message,
        conversation_history: List[Message]
    ) -> str:
        """
        Generate a human-like response to the scammer's message
        
        Args:
            current_message: Current message from scammer
            conversation_history: Previous messages in conversation
            
        Returns:
            Agent's response as a user would respond
        """
        # Build conversation context
        all_messages = conversation_history + [current_message]
        context = self._build_conversation_context(all_messages)
        
        # Get agent prompt with context
        system_prompt = get_agent_prompt(context)
        
        try:
            # Generate response using OpenAI
            response = await self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Scammer just said: \"{current_message.text}\"\n\nRespond naturally as a regular person would."}
                ],
                temperature=config.OPENAI_TEMPERATURE,
                max_tokens=150,  # Keep responses short
            )
            
            reply = response.choices[0].message.content.strip()
            
            # Ensure response isn't too long (SMS-like)
            if len(reply) > 300:
                # Truncate to first 1-2 sentences
                sentences = reply.split('.')
                reply = sentences[0] + ('.' if len(sentences) > 1 else '')
            
            return reply
        
        except Exception as e:
            print(f"Error generating AI response: {e}")
            # Fallback responses based on conversation state
            return self._get_fallback_response(current_message, conversation_history)
    
    def _get_fallback_response(
        self,
        current_message: Message,
        conversation_history: List[Message]
    ) -> str:
        """
        Get a fallback response if AI generation fails
        
        Args:
            current_message: Current message
            conversation_history: Previous messages
            
        Returns:
            Fallback response string
        """
        message_lower = current_message.text.lower()
        
        # First message responses
        if not conversation_history:
            if any(word in message_lower for word in ["bank", "account"]):
                return "Wait, which bank account are you talking about?"
            elif "upi" in message_lower:
                return "What about my UPI? Can you explain?"
            elif any(word in message_lower for word in ["blocked", "suspended"]):
                return "Why would it be blocked??"
            else:
                return "I don't understand. Can you explain what this is about?"
        
        # Follow-up responses
        if "link" in message_lower or "http" in message_lower:
            return "Ok send me the link"
        elif "call" in message_lower or "contact" in message_lower:
            return "What number should I call?"
        elif any(word in message_lower for word in ["payment", "pay", "transfer"]):
            return "Where do I send the payment?"
        else:
            return "Can you give me more details about this?"
    
    async def generate_context_aware_response(
        self,
        current_message: Message,
        conversation_history: List[Message],
        scam_categories: List[str]
    ) -> tuple[str, str]:
        """
        Generate response with agent notes about the interaction
        
        Args:
            current_message: Current message from scammer
            conversation_history: Previous messages
            scam_categories: Detected scam categories
            
        Returns:
            Tuple of (response, agent_notes)
        """
        response = await self.generate_response(current_message, conversation_history)
        
        # Generate agent notes based on scam categories
        notes = self._generate_notes(current_message, scam_categories)
        
        return response, notes
    
    def _generate_notes(self, message: Message, categories: List[str]) -> str:
        """
        Generate notes about scammer behavior
        
        Args:
            message: Current message
            categories: Detected scam categories
            
        Returns:
            Notes string
        """
        notes_parts = []
        
        if "urgency" in categories:
            notes_parts.append("Used urgency tactics")
        
        if "threat" in categories:
            notes_parts.append("Employed threats")
        
        if "banking" in categories:
            notes_parts.append("Banking/financial scam")
        
        if "phishing_link" in categories:
            notes_parts.append("Shared suspicious links")
        
        if "reward" in categories:
            notes_parts.append("Prize/reward scam")
        
        if "verification" in categories:
            notes_parts.append("Verification/authentication attempt")
        
        if "sensitive_info_request" in categories:
            notes_parts.append("Requested sensitive information")
        
        # Add general note about message content
        message_lower = message.text.lower()
        if any(word in message_lower for word in ["otp", "pin", "cvv", "password"]):
            notes_parts.append("Asked for credentials")
        
        return "; ".join(notes_parts) if notes_parts else "Scam attempt detected"
