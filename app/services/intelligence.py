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
    # This catches +11..., +91..., and standalone numbers 7-15 digits long.
    # We remove the [6-9] restriction to allow numbers starting with 2, 3, etc.
    PHONE_PATTERN = re.compile(r'(?:\+\d{1,3}\s?|0)?\d{7,10}\b')

    # 4. BANK ACCOUNT: 
    # 11-18 digits. We rely on length and context in the logic to separate this from phones.
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
    
    def extract_from_text(self, text: str) -> None:
        """
        Extract intelligence from a single text message
        
        Args:
            text: Message text to analyze
        """
        text_lower = text.lower()
        
        # Extract bank accounts
        bank_accounts = self.BANK_ACCOUNT_PATTERN.finditer(text)
        account_spans = []
        for match in bank_accounts:
            account = match.group()
            account_spans.append(match.span()) # Save location to prevent phone overlap
            if account not in self.extracted.bankAccounts:
                self.extracted.bankAccounts.append(account)
        # Extract UPI IDs
        upi_ids = self.UPI_ID_PATTERN.findall(text)
        for upi_id in upi_ids:
            if '@' in upi_id and upi_id not in self.extracted.upiIds:
                self.extracted.upiIds.append(upi_id)
        
        # Extract phone numbers
        phones = self.PHONE_PATTERN.findall(text)
        for phone in phones:
            # Clean up phone number
            clean_phone = re.sub(r'[-.\s()]', '', phone)
            if len(clean_phone) >= 10 and clean_phone not in self.extracted.phoneNumbers:
                self.extracted.phoneNumbers.append(phone.strip())
        
        # Extract URLs
        urls = self.URL_PATTERN.findall(text)
        for url in urls:
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
        
        Args:
            messages: List of messages to analyze
        """
        for message in messages:
            self.extract_from_text(message.text)
    
    def get_extracted_intelligence(self) -> ExtractedIntelligence:
        """
        Get all extracted intelligence
        
        Returns:
            ExtractedIntelligence object with all extracted data
        """
        return self.extracted
    
    def has_significant_intelligence(self, min_items: int = 3) -> bool:
        """
        Check if significant intelligence has been extracted
        
        Args:
            min_items: Minimum number of intelligence items to consider significant
            
        Returns:
            True if significant intelligence extracted
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
        
        Returns:
            Human-readable summary string
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
        
        Args:
            other: Another ExtractedIntelligence to merge
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
