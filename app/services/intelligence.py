"""
Intelligence extraction from scammer conversations
"""
import re
from typing import List, Set
from app.models import ExtractedIntelligence, Message

class IntelligenceExtractor:
    """Extract intelligence from scammer messages"""
    
    # 1. URL: Supports http, https, and www
    URL_PATTERN = re.compile(r'\b(?:https?://\S+|www\.\S+)\b', re.IGNORECASE)

    # 2. UPI: Stays the same
    UPI_ID_PATTERN = re.compile(r'\b[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\b')

    # 3. GLOBAL PHONE: 
    PHONE_PATTERN = re.compile(r'(?:\+\d{1,3}\s?|0)?\d{7,10}(?!\d)')

    # 4. BANK ACCOUNT: 
    BANK_ACCOUNT_PATTERN = re.compile(r'(?<!\d)\d{11,18}(?!\d)')
    
    # Suspicious keywords to track
    SUSPICIOUS_KEYWORDS = {
        # Urgency
        "urgent", "immediately", "now", "today", "asap", "hurry", "quick", "fast",
        # Verification/Security
        "verify", "confirm", "authenticate", "validate", "security", "alert",
        # Account issues
        "blocked", "suspended", "locked", "frozen", "deactivated", "expired",
        # Banking terms
        "bank", "account", "upi", "payment", "transfer", "transaction",
        "otp", "cvv", "pin", "password", "atm", "card", "debit", "credit",
        # Threats
        "legal action", "police", "arrest", "fine", "penalty", "court",
        # Rewards
        "prize", "winner", "won", "lottery", "reward", "cashback", "refund",
        # Links
        "click here", "link", "website", "portal", "login",
        # Personal info requests
        "share", "send", "provide", "details", "information", "data"
    }
    
    def __init__(self):
        self.extracted: ExtractedIntelligence = ExtractedIntelligence()

    def _is_user_context(self, text: str, match_span: tuple, window_size: int = 35) -> bool:
        """
        Check if the extracted item is near words indicating it belongs 
        to the user rather than the scammer (e.g., "your account", "is this yours?").
        """
        start_idx, end_idx = match_span
        
        # Look behind the match
        start = max(0, start_idx - window_size)
        preceding_text = text[start:start_idx].lower()
        
        # Look ahead of the match (e.g., "1234567890 is your number?")
        end = min(len(text), end_idx + 20)
        following_text = text[end_idx:end].lower()
        
        # Words that indicate the data belongs to the user or the bot
        exclusion_pattern = r'\b(your|yours|my|mine)\b'
        
        if re.search(exclusion_pattern, preceding_text) or re.search(exclusion_pattern, following_text):
            return True
            
        return False
    
    def extract_from_text(self, text: str) -> None:
        """
        Extract intelligence from a single text message
        """
        text_lower = text.lower()
        
        # Extract bank accounts
        bank_accounts = self.BANK_ACCOUNT_PATTERN.finditer(text)
        account_spans = []
        for match in bank_accounts:
            # Skip if it is referenced as the user's account
            if self._is_user_context(text, match.span()):
                continue
                
            account = match.group()
            account_spans.append(match.span()) # Save location to prevent phone overlap
            if account not in self.extracted.bankAccounts:
                self.extracted.bankAccounts.append(account)
                
        # Extract UPI IDs (Changed to finditer to check position context)
        upi_ids = self.UPI_ID_PATTERN.finditer(text)
        for match in upi_ids:
            if self._is_user_context(text, match.span()):
                continue
                
            upi_id = match.group()
            if '@' in upi_id and upi_id not in self.extracted.upiIds:
                self.extracted.upiIds.append(upi_id)
        
        # Extract phone numbers
        phone_matches = self.PHONE_PATTERN.finditer(text)
        for match in phone_matches:
            if self._is_user_context(text, match.span()):
                continue
                
            phone = match.group()
            phone_span = match.span()
            
            # Check if this phone match is actually just a part of a bank account
            is_sub_match = any(phone_span[0] >= s[0] and phone_span[1] <= s[1] for s in account_spans)
            
            if not is_sub_match:
                clean_phone = re.sub(r'[-.\s()]', '', phone)
                if len(clean_phone) >= 7 and phone.strip() not in self.extracted.phoneNumbers:
                    self.extracted.phoneNumbers.append(phone.strip())
                    
        # Extract URLs (Changed to finditer to check position context)
        urls = self.URL_PATTERN.finditer(text)
        for match in urls:
            if self._is_user_context(text, match.span()):
                continue
                
            url = match.group()
            if url not in self.extracted.phishingLinks:
                self.extracted.phishingLinks.append(url)
        
        # Extract suspicious keywords
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in text_lower:
                if keyword not in self.extracted.suspiciousKeywords:
                    self.extracted.suspiciousKeywords.append(keyword)
    
    def extract_from_messages(self, messages: List[Message]) -> None:
        """
        Extract intelligence from a list of messages
        """
        for message in messages:
            self.extract_from_text(message.text)
    
    def get_extracted_intelligence(self) -> ExtractedIntelligence:
        """
        Get all extracted intelligence
        """
        return self.extracted
    
    def has_significant_intelligence(self, min_items: int = 3) -> bool:
        """
        Check if significant intelligence has been extracted
        """
        total_items = (
            len(self.extracted.bankAccounts) +
            len(self.extracted.upiIds) +
            len(self.extracted.phoneNumbers) +
            len(self.extracted.phishingLinks)
        )
        return total_items >= min_items
    
    def get_intelligence_summary(self) -> str:
        """
        Get a summary of extracted intelligence
        """
        items = []
        
        if self.extracted.bankAccounts:
            items.append(f"{len(self.extracted.bankAccounts)} bank account(s)")
        if self.extracted.upiIds:
            items.append(f"{len(self.extracted.upiIds)} UPI ID(s)")
        if self.extracted.phoneNumbers:
            items.append(f"{len(self.extracted.phoneNumbers)} phone number(s)")
        if self.extracted.phishingLinks:
            items.append(f"{len(self.extracted.phishingLinks)} suspicious link(s)")
        
        if not items:
            return "No intelligence extracted yet"
        
        return f"Extracted: {', '.join(items)}"
    
    def merge_intelligence(self, other: ExtractedIntelligence) -> None:
        """
        Merge intelligence from another ExtractedIntelligence object
        """
        # Merge bank accounts
        for account in other.bankAccounts:
            if account not in self.extracted.bankAccounts:
                self.extracted.bankAccounts.append(account)
        
        # Merge UPI IDs
        for upi_id in other.upiIds:
            if upi_id not in self.extracted.upiIds:
                self.extracted.upiIds.append(upi_id)
        
        # Merge phone numbers
        for phone in other.phoneNumbers:
            if phone not in self.extracted.phoneNumbers:
                self.extracted.phoneNumbers.append(phone)
        
        # Merge phishing links
        for link in other.phishingLinks:
            if link not in self.extracted.phishingLinks:
                self.extracted.phishingLinks.append(link)
        
        # Merge keywords
        for keyword in other.suspiciousKeywords:
            if keyword not in self.extracted.suspiciousKeywords:
                self.extracted.suspiciousKeywords.append(keyword)