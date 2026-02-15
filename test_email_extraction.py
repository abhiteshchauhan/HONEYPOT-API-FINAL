"""
Quick test for email extraction and model changes
"""
from app.services.intelligence import IntelligenceExtractor
from app.models import ExtractedIntelligence

# Test email extraction
extractor = IntelligenceExtractor()

test_text = """
Contact us at support@scammer.com or call 9876543210.
Send payment to scammer@fake.com or UPI: fraud@paytm
Visit http://fake-site.com for more info.
Account: 12345678901234
"""

extractor.extract_from_text(test_text)
intelligence = extractor.get_extracted_intelligence()

print("Testing Email Extraction and Model Structure")
print("=" * 60)
print(f"Phone Numbers: {intelligence.phoneNumbers}")
print(f"Bank Accounts: {intelligence.bankAccounts}")
print(f"UPI IDs: {intelligence.upiIds}")
print(f"Phishing Links: {intelligence.phishingLinks}")
print(f"Email Addresses: {intelligence.emailAddresses}")
print(f"Suspicious Keywords: {intelligence.suspiciousKeywords}")
print("=" * 60)

# Test model serialization
print("\nModel JSON Output:")
print(intelligence.model_dump_json(indent=2))
