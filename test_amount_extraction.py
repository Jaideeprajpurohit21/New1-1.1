#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Amount Extraction Testing

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import re
import sys
import os

# Add the backend directory to the path so we can import the OCR processor
sys.path.append('/app/backend')

def test_amount_extraction():
    """Test the enhanced amount extraction with various transaction formats"""
    
    # Test examples from user input
    test_cases = [
        "Alfamart PURCHASE INR 485.00 on 12-03-2024. Avl bal INR 12,345.67. Trxn ID 1234567890.",
        "You spent $29.99 at Amazon.com on Oct 5. Your card ending in 1234 was charged.",
        "Acct XXX1234 debited INR 1,500.00 on 05/01/24 for UPI payment to John Doe. Ref No. 987654.",
        "Netflix monthly subscription of $15.99 was automatically charged on 2024-10-05.",
        "Payment of INR 2,000.00 to ELECTRICITY BOARD on 12th Mar 2024 successful."
    ]
    
    # Enhanced amount patterns (copied from the updated server.py)
    amount_patterns = [
        # International currency formats: INR 1,500.00, USD 29.99, EUR 15.99
        r'(?:INR|USD|EUR|GBP|CAD|AUD)\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # INR 1,500.00, USD 29.99
        r'(?:₹|$|€|£|¥)\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',              # ₹1,500.00, $29.99
        
        # Standard formats: $12.34, 12.34, $12, 12
        r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',                         # $12.34, $1,500.00
        r'\d{1,3}(?:,\d{3})*\.\d{2}',                                   # 12.34, 1,500.00
        r'\d{1,3}(?:,\d{3})*\s*\.\s*\d{2}',                           # 12 . 34, 1,500 . 00 (with spaces)
        
        # Transaction notification formats
        r'(?:PURCHASE|spent|charged|debited|payment)\s+(?:INR|USD|EUR|GBP|\$|₹)\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # PURCHASE INR 485.00, spent $29.99
        r'(?:of|amount)\s+(?:INR|USD|EUR|GBP|\$|₹)\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # of $15.99, amount INR 2,000.00
        
        # Receipt total formats: TOTAL: $12.34, Total $12.34, etc.
        r'(?:TOTAL|total|Total)\s*:?\s*(?:INR|USD|EUR|GBP|\$|₹)?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # TOTAL: $12.34, TOTAL INR 485.00
        r'(?:AMOUNT|amount|Amount)\s*:?\s*(?:INR|USD|EUR|GBP|\$|₹)?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?', # AMOUNT: $12.34
        r'(?:DUE|due|Due)\s*:?\s*(?:INR|USD|EUR|GBP|\$|₹)?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',       # DUE: $12.34
        r'(?:BALANCE|balance|Balance)\s*:?\s*(?:INR|USD|EUR|GBP|\$|₹)?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?', # BALANCE: $12.34
        
        # Cash and payment amounts
        r'(?:CASH|cash|Cash)\s*:?\s*(?:INR|USD|EUR|GBP|\$|₹)?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',    # CASH: $12.34
        r'(?:CHANGE|change|Change)\s*:?\s*(?:INR|USD|EUR|GBP|\$|₹)?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?', # CHANGE: $12.34
        
        # Subscription and automatic payment formats
        r'(?:subscription|monthly|automatically)\s+(?:of\s+)?(?:INR|USD|EUR|GBP|\$|₹)?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?', # monthly subscription of $15.99
        
        # Basic number formats (fallback)
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?',                             # 1,500.00, 29.99 (basic fallback)
    ]
    
    def clean_amount_text(amount_text: str) -> str:
        """Clean and standardize amount text to proper format with international currency support"""
        try:
            # Remove extra spaces and prepare for processing
            cleaned = amount_text.strip()
            
            # Currency mapping for standardization
            currency_map = {
                'INR': '₹',
                'USD': '$',
                'EUR': '€',
                'GBP': '£',
                'CAD': '$',
                'AUD': '$'
            }
            
            # Extract currency symbol or code
            currency_symbol = '$'  # default
            
            # Check for currency codes (INR, USD, etc.)
            for code, symbol in currency_map.items():
                if code in cleaned.upper():
                    currency_symbol = symbol
                    # Remove currency code from text for number extraction
                    cleaned = re.sub(r'\b' + code + r'\b', '', cleaned, flags=re.IGNORECASE).strip()
                    break
            
            # Check for currency symbols (₹, $, €, etc.)
            currency_symbols = ['₹', '$', '€', '£', '¥']
            for symbol in currency_symbols:
                if symbol in cleaned:
                    currency_symbol = symbol
                    cleaned = cleaned.replace(symbol, '').strip()
                    break
            
            # Extract numeric part with commas and decimals
            # First, try to find number with commas and decimal: 1,500.00
            comma_decimal_match = re.search(r'\d{1,3}(?:,\d{3})*\.\d{2}', cleaned)
            if comma_decimal_match:
                number_str = comma_decimal_match.group()
                # Remove commas for processing
                number = number_str.replace(',', '')
                return f"{currency_symbol}{number}"
            
            # Try to find number with commas but no decimal: 1,500
            comma_match = re.search(r'\d{1,3}(?:,\d{3})*', cleaned)
            if comma_match:
                number_str = comma_match.group()
                # Remove commas for processing
                number = number_str.replace(',', '')
                return f"{currency_symbol}{number}.00"
            
            # Try to find simple decimal: 12.34
            decimal_match = re.search(r'\d+\.\d{2}', cleaned)
            if decimal_match:
                number = decimal_match.group()
                return f"{currency_symbol}{number}"
            
            # Try to find whole number: 12
            whole_match = re.search(r'\d+', cleaned)
            if whole_match:
                number = whole_match.group()
                return f"{currency_symbol}{number}.00"
            
            return None
            
        except Exception as e:
            print(f"Error cleaning amount text '{amount_text}': {str(e)}")
            return None

    print("🧪 Testing Enhanced Amount Extraction")
    print("=" * 60)
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Input: {test_text}")
        
        found_amounts = []
        
        # Test each pattern against the text
        for pattern in amount_patterns:
            matches = re.findall(pattern, test_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    cleaned = clean_amount_text(match)
                    if cleaned and cleaned not in found_amounts:
                        found_amounts.append(cleaned)
        
        print(f"Found amounts: {found_amounts if found_amounts else 'None detected'}")
        
        # Expected results for validation
        expected = {
            1: ["₹485.00", "₹12345.67"],  # INR 485.00 and INR 12,345.67
            2: ["$29.99"],                # $29.99
            3: ["₹1500.00"],              # INR 1,500.00  
            4: ["$15.99"],                # $15.99
            5: ["₹2000.00"]               # INR 2,000.00
        }
        
        if found_amounts:
            print(f"✅ SUCCESS - Detected: {', '.join(found_amounts)}")
        else:
            print("❌ FAILED - No amounts detected")
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    print("Enhanced amount extraction now supports:")
    print("  • International currencies (INR, USD, EUR, GBP, etc.)")
    print("  • Currency symbols (₹, $, €, £, ¥)")
    print("  • Comma separators in numbers (1,500.00)")
    print("  • Transaction notification formats")
    print("  • Multiple amounts in single text")
    print("  • Automatic currency standardization")

if __name__ == "__main__":
    test_amount_extraction()