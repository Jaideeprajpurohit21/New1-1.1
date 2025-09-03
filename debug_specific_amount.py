#!/usr/bin/env python3
"""Debug specific amount pattern"""

from robust_amount_extractor import extract_amount
import re

text = "Amount: 25.50"
print(f"Testing: '{text}'")

# Test individual patterns manually
patterns = [
    r'\b(?:INR|USD|EUR|GBP|CAD|AUD|SGD|JPY)\s+\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b',
    r'[₹$€£¥¢]\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?(?!\d)',
    r'\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?',
]

for i, pattern in enumerate(patterns):
    matches = re.finditer(pattern, text, re.IGNORECASE)
    print(f"Pattern {i+1}: {pattern}")
    for match in matches:
        print(f"  Found: '{match.group()}' at position {match.start()}-{match.end()}")

# Test the actual function
result = extract_amount(text)
print(f"extract_amount result: {result}")

# Test with currency symbol
text_with_symbol = "Amount: $25.50"
result_with_symbol = extract_amount(text_with_symbol)
print(f"extract_amount with symbol: {result_with_symbol}")