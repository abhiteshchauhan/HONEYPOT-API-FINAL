"""
Intelligence extraction from scammer conversations
"""
import re
from typing import List, Set
from app.models import ExtractedIntelligence, Message
from app.services.filter import is_scammer_data

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


    
    async def extract_from_text(self, text: str) -> None:
        text_lower = text.lower()
        
        bank_accounts = self.BANK_ACCOUNT_PATTERN.finditer(text)
        account_spans = []
        for match in bank_accounts:
            account = match.group()
            account_spans.append(match.span())
            if await is_scammer_data(text, account, "bank account"):
                if account not in self.extracted.bankAccounts:
                    self.extracted.bankAccounts.append(account)
                    
        upi_ids = self.UPI_ID_PATTERN.finditer(text)
        for match in upi_ids:
            upi_id = match.group()
            if '@' in upi_id:
                if await is_scammer_data(text, upi_id, "UPI ID"):
                    if upi_id not in self.extracted.upiIds:
                        self.extracted.upiIds.append(upi_id)
        
        phone_matches = self.PHONE_PATTERN.finditer(text)
        for match in phone_matches:
            phone = match.group()
            phone_span = match.span()
            
            is_sub_match = any(phone_span[0] >= s[0] and phone_span[1] <= s[1] for s in account_spans)
            
            if not is_sub_match:
                if await is_scammer_data(text, phone, "phone number"):
                    clean_phone = re.sub(r'[-.\s()]', '', phone)
                    if len(clean_phone) >= 7 and phone.strip() not in self.extracted.phoneNumbers:
                        self.extracted.phoneNumbers.append(phone.strip())
                        
        urls = self.URL_PATTERN.finditer(text)
        for match in urls:
            url = match.group()
            if await is_scammer_data(text, url, "URL"):
                if url not in self.extracted.phishingLinks:
                    self.extracted.phishingLinks.append(url)
        
        # Extract suspicious keywords
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in text_lower:
                if keyword not in self.extracted.suspiciousKeywords:
                    self.extracted.suspiciousKeywords.append(keyword)
    
    async def extract_from_messages(self, messages: List[Message]) -> None:
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