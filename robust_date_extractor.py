#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Robust Date Extractor

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import re
from datetime import datetime, date
from typing import Optional, List, Tuple
import calendar

def extract_date(text: str) -> Optional[str]:
    """
    Robust function to extract transaction dates from text while avoiding 
    false matches with amounts, IDs, and other numbers.
    
    Args:
        text (str): Input text containing date information
        
    Returns:
        Optional[str]: The most likely transaction date in YYYY-MM-DD format, or None if not found
    """
    
    if not text or not isinstance(text, str):
        return None
    
    # Current date for validation
    today = date.today()
    current_year = today.year
    
    # Month name mappings
    month_names = {
        'january': 1, 'jan': 1, 'februari': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    # Date context keywords that suggest nearby text contains a date
    date_keywords = [
        'on', 'date', 'dated', 'transaction', 'charged', 'billed', 'purchased',
        'payment', 'transfer', 'withdrawal', 'deposit', 'processed', 'completed',
        'time', 'when', 'was', 'billing', 'next'
    ]
    
    # Keywords to avoid (these typically indicate non-date contexts)
    avoid_keywords = [
        'amount', 'balance', 'total', 'price', 'cost', 'fee', 'limit', 
        'account', 'card', 'number', 'id', 'phone', 'mobile', 'contact'
    ]
    
    def validate_date(year: int, month: int, day: int) -> bool:
        """Validate if the date is reasonable for a transaction"""
        try:
            # Check if date is valid
            test_date = date(year, month, day)
            
            # Date should not be in the future (allow up to 1 day for timezone differences)
            if test_date > today:
                return False
            
            # Date should not be too old (transactions older than 10 years are unlikely)
            if year < current_year - 10:
                return False
            
            return True
        except ValueError:
            return False
    
    def parse_date_with_priority(candidates: List[Tuple[str, int, int]]) -> Optional[str]:
        """Parse date candidates with priority scoring (lower score = higher priority)"""
        valid_dates = []
        
        for date_str, priority, position in candidates:
            parsed_date = parse_single_date(date_str)
            if parsed_date:
                valid_dates.append((parsed_date, priority, position))
        
        if valid_dates:
            # Sort by priority, then by position (earlier in text = higher priority)
            valid_dates.sort(key=lambda x: (x[1], x[2]))
            return valid_dates[0][0]
        
        return None
    
    def parse_single_date(date_str: str) -> Optional[str]:
        """Parse a single date string and return YYYY-MM-DD format"""
        date_str = date_str.strip()
        
        # Pattern 1: YYYY-MM-DD or YYYY/MM/DD
        match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if validate_date(year, month, day):
                return f"{year:04d}-{month:02d}-{day:02d}"
        
        # Pattern 2: DD-MM-YYYY or DD/MM/YYYY
        match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', date_str)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if validate_date(year, month, day):
                return f"{year:04d}-{month:02d}-{day:02d}"
        
        # Pattern 3: MM/DD/YY or MM-DD-YY (US format)
        match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{2})', date_str)
        if match:
            month, day, year_short = int(match.group(1)), int(match.group(2)), int(match.group(3))
            # Convert 2-digit year to 4-digit (assume 20xx for years 00-30, 19xx for 31-99)
            year = 2000 + year_short if year_short <= 30 else 1900 + year_short
            if month <= 12 and validate_date(year, month, day):
                return f"{year:04d}-{month:02d}-{day:02d}"
        
        # Pattern 4: DD/MM/YY or DD-MM-YY (European format)
        match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{2})', date_str)
        if match:
            day, month, year_short = int(match.group(1)), int(match.group(2)), int(match.group(3))
            year = 2000 + year_short if year_short <= 30 else 1900 + year_short
            # Only use this if day > 12 (to distinguish from US format)
            if day > 12 and validate_date(year, month, day):
                return f"{year:04d}-{month:02d}-{day:02d}"
        
        # Pattern 5: Textual dates like "Oct 5" or "5 Oct" or "October 5, 2024"
        for month_name, month_num in month_names.items():
            # Format: "Oct 5" or "October 5" (without year - use current year)
            pattern = rf'\b{re.escape(month_name)}\s+(\d{{1,2}})\b(?!\s*,?\s*\d{{4}})'
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                day = int(match.group(1))
                year = current_year  # Use current year
                # But if the date would be in future, use previous year
                test_date = date(year, month_num, day)
                if test_date > today:
                    year = current_year - 1
                if validate_date(year, month_num, day):
                    return f"{year:04d}-{month_num:02d}-{day:02d}"
            
            # Format: "5 Oct" or "5 October" (without year)
            pattern = rf'\b(\d{{1,2}})\s+{re.escape(month_name)}\b(?!\s*\d{{4}})'
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                day = int(match.group(1))
                year = current_year
                test_date = date(year, month_num, day)
                if test_date > today:
                    year = current_year - 1
                if validate_date(year, month_num, day):
                    return f"{year:04d}-{month_num:02d}-{day:02d}"
            
            # Format: "Oct 5, 2024" or "October 5, 2024"
            pattern = rf'\b{re.escape(month_name)}\s+(\d{{1,2}}),?\s+(\d{{4}})\b'
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                day, year = int(match.group(1)), int(match.group(2))
                if validate_date(year, month_num, day):
                    return f"{year:04d}-{month_num:02d}-{day:02d}"
            
            # Format: "5th Oct 2024" or "12th Mar 2024"
            pattern = rf'\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{re.escape(month_name)}\s+(\d{{4}})\b'
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                day, year = int(match.group(1)), int(match.group(2))
                if validate_date(year, month_num, day):
                    return f"{year:04d}-{month_num:02d}-{day:02d}"
        
        return None
    
    # Find all potential date candidates with context scoring
    candidates = []
    text_lower = text.lower()
    
    # Priority 0: Dates near date keywords (highest priority)
    for keyword in date_keywords:
        for match in re.finditer(re.escape(keyword), text_lower):
            start_pos = max(0, match.start() - 30)
            end_pos = min(len(text), match.end() + 30)
            context_window = text[start_pos:end_pos]
            
            # Look for date patterns in this window
            date_patterns = [
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',     # YYYY-MM-DD
                r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',     # DD-MM-YYYY
                r'\d{1,2}[-/]\d{1,2}[-/]\d{2}',     # MM/DD/YY or DD/MM/YY
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,?\s+\d{4})?\b',  # Oct 5 2024
                r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b'  # 5th Oct 2024
            ]
            
            for pattern in date_patterns:
                for date_match in re.finditer(pattern, context_window, re.IGNORECASE):
                    date_str = date_match.group()
                    distance = abs(date_match.start() - (match.start() - start_pos))
                    priority = distance  # Lower distance = higher priority
                    position = start_pos + date_match.start()
                    candidates.append((date_str, priority, position))
    
    # Priority 1: Dates in ISO-like formats (medium priority)
    iso_patterns = [
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',
        r'\b\d{4}/\d{1,2}/\d{1,2}\b'
    ]
    
    for pattern in iso_patterns:
        for match in re.finditer(pattern, text):
            # Skip if this looks like it's in a monetary context
            context_start = max(0, match.start() - 20)
            context_end = min(len(text), match.end() + 20)
            context = text[context_start:context_end].lower()
            
            if any(avoid_word in context for avoid_word in avoid_keywords):
                continue
            
            candidates.append((match.group(), 1000, match.start()))
    
    # Priority 2: Other date formats (lower priority)
    other_patterns = [
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b',
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2}\b'
    ]
    
    for pattern in other_patterns:
        for match in re.finditer(pattern, text):
            context_start = max(0, match.start() - 20)
            context_end = min(len(text), match.end() + 20)
            context = text[context_start:context_end].lower()
            
            if any(avoid_word in context for avoid_word in avoid_keywords):
                continue
            
            candidates.append((match.group(), 2000, match.start()))
    
    # Priority 3: Textual dates (lowest priority for fallback)
    month_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,?\s+\d{4})?\b'
    for match in re.finditer(month_pattern, text, re.IGNORECASE):
        candidates.append((match.group(), 3000, match.start()))
    
    # Parse candidates and return the best match
    return parse_date_with_priority(candidates)


def test_extract_date():
    """Comprehensive test suite for the extract_date function"""
    
    test_cases = [
        # Basic date formats
        {
            'input': "Alfamart PURCHASE INR 485.00 on 12-03-2024. Avl bal INR 12,345.67. Trxn ID 1234567890.",
            'expected': "2024-03-12",
            'description': "DD-MM-YYYY format in transaction text"
        },
        {
            'input': "You spent $29.99 at Amazon.com on Oct 5. Your card ending in 1234 was charged.",
            'expected': f"{datetime.now().year}-10-05",
            'description': "Month name format (Oct 5)"
        },
        {
            'input': "Acct XXX1234 debited INR 1,500.00 on 05/01/24 for UPI payment to John Doe. Ref No. 987654.",
            'expected': "2024-01-05",
            'description': "MM/DD/YY format (US style)"
        },
        {
            'input': "Netflix monthly subscription of $15.99 was automatically charged on 2024-10-05.",
            'expected': "2024-10-05",
            'description': "ISO format YYYY-MM-DD"
        },
        {
            'input': "Payment of INR 2,000.00 to ELECTRICITY BOARD on 12th Mar 2024 successful.",
            'expected': "2024-03-12",
            'description': "Ordinal date format (12th Mar 2024)"
        },
        
        # Edge cases with multiple numbers
        {
            'input': "Card 4567 charged $125.50 on 15/12/2024. Balance: $1,234.56. Ref: 789012",
            'expected': "2024-12-15",
            'description': "Date with card numbers and amounts"
        },
        {
            'input': "Mobile recharge ₹299 on December 15, 2024. Phone: 9876543210. ID: 12345",
            'expected': "2024-12-15",
            'description': "Full month name with phone number and ID"
        },
        {
            'input': "Transaction 98765 processed on Aug 23, 2024 for amount $567.89",
            'expected': "2024-08-23",
            'description': "Month name with transaction ID and amount"
        },
        {
            'input': "Wire transfer $5,000.00 on 2024/11/20. Reference: 1234567890123456",
            'expected': "2024-11-20",
            'description': "YYYY/MM/DD format with large reference number"
        },
        
        # Different date contexts
        {
            'input': "Hotel booking confirmed for 25 Nov 2024. Total: €189.50. Confirmation: 98765",
            'expected': "2024-11-25",
            'description': "Date with confirmation number"
        },
        {
            'input': "Subscription billed on 01-01-2024. Next billing: 01-02-2024. Amount: $19.99",
            'expected': "2024-01-01",
            'description': "Multiple dates - should pick first transaction-related"
        },
        {
            'input': "Payment due 30/06/24. Account: 1234567890. Late fee: $25.00",
            'expected': "2024-06-30",
            'description': "Due date with account number"
        },
        
        # European vs US date format disambiguation
        {
            'input': "Transaction on 25/12/2024. Amount: $100.00. Card: 4567",
            'expected': "2024-12-25",
            'description': "European date format (day > 12)"
        },
        {
            'input': "Purchase on 08/05/24. Total: ₹750.00. Store ID: 9876",
            'expected': "2024-05-08",
            'description': "Ambiguous date format (could be May 8 or Aug 5)"
        },
        
        # Invalid/no dates
        {
            'input': "Account balance: $1,234.56. Card ending: 5678. Customer ID: 98765",
            'expected': None,
            'description': "No date present, only numbers"
        },
        {
            'input': "Call customer service at 1-800-555-0123. Account: 9876543210",
            'expected': None,
            'description': "Phone number and account, no date"
        },
        
        # Future dates (should be rejected)
        {
            'input': f"Subscription renews on 01-01-{datetime.now().year + 2}. Amount: $29.99",
            'expected': None,
            'description': "Future date should be rejected"
        },
        
        # Very old dates (should be rejected)
        {
            'input': "Historical transaction on 01-01-2010. Amount: $50.00",
            'expected': None,
            'description': "Very old date should be rejected"
        },
        
        # Different month name formats
        {
            'input': "Charged on September 15, 2024. Amount: £75.99",
            'expected': "2024-09-15",
            'description': "Full month name"
        },
        {
            'input': "Payment processed 15 Sep 2024. Card: 1234",
            'expected': "2024-09-15",
            'description': "Abbreviated month name (day first)"
        }
    ]
    
    print("🗓️ Testing Robust Date Extractor")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        input_text = test_case['input']
        expected = test_case['expected']
        description = test_case['description']
        
        result = extract_date(input_text)
        
        print(f"\n📝 Test {i}: {description}")
        print(f"Input: {input_text}")
        print(f"Expected: {expected}")
        print(f"Got: {result}")
        
        success = result == expected
        
        if success:
            print("✅ PASSED")
            passed += 1
        else:
            print("❌ FAILED")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    print(f"Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    return passed == len(test_cases)


def combined_extractor_demo():
    """Demonstrate combined amount and date extraction"""
    
    # Import the amount extractor
    try:
        from robust_amount_extractor import extract_amount
    except ImportError:
        print("⚠️ Amount extractor not available for demo")
        return
    
    demo_texts = [
        "Alfamart PURCHASE INR 485.00 on 12-03-2024. Avl bal INR 12,345.67. Trxn ID 1234567890.",
        "You spent $29.99 at Amazon.com on Oct 5. Your card ending in 1234 was charged.",
        "Netflix monthly subscription of $15.99 was automatically charged on 2024-10-05.",
        "Payment of INR 2,000.00 to ELECTRICITY BOARD on 12th Mar 2024 successful."
    ]
    
    print("\n" + "=" * 70)
    print("🔄 Combined Amount & Date Extraction Demo")
    print("=" * 70)
    
    for i, text in enumerate(demo_texts, 1):
        print(f"\n📄 Sample {i}:")
        print(f"Text: {text}")
        
        amount = extract_amount(text)
        date_extracted = extract_date(text)
        
        print(f"💰 Amount: {amount}")
        print(f"📅 Date: {date_extracted}")
        print(f"✨ Combined: Transaction of {amount} on {date_extracted}")


if __name__ == "__main__":
    # Run the test suite
    success = test_extract_date()
    
    if success:
        print("\n🎉 All tests passed! The extract_date function is robust and ready.")
    else:
        print("\n⚠️ Some tests failed. Review the function logic.")
    
    # Run combined demo
    combined_extractor_demo()