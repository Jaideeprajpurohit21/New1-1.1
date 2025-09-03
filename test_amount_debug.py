#!/usr/bin/env python3
"""Debug amount extraction"""

from robust_amount_extractor import extract_amount
from transaction_processor import TransactionProcessor

# Test some sample texts
test_texts = [
    "Total: $15.99",
    "Amount: 25.50",
    "TOTAL $123.45",
    "Paid 45.67",
    "Charge: $9.99",
    "Error: Failed to convert PDF to images"
]

print("🔍 Testing amount extraction:")
for text in test_texts:
    amount = extract_amount(text)
    print(f"  '{text}' → ${amount}")

print("\n🔍 Testing transaction processor:")
processor = TransactionProcessor()
for text in test_texts:
    result = processor.process_transaction(text)
    print(f"  '{text}' → Amount: {result.get('amount')}, Category: {result.get('category')}")