#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Robust Amount Extractor

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import re
from typing import Optional, List, Tuple

def extract_amount(text: str) -> Optional[float]:
    """
    Robust function to extract transaction amounts from text while ignoring 
    account balances, transaction IDs, and other irrelevant numbers.
    
    Args:
        text (str): Input text containing transaction information
        
    Returns:
        Optional[float]: The most likely transaction amount as float, or None if not found
    """
    
    if not text or not isinstance(text, str):
        return None
    
    # Normalize text for processing
    text = text.strip()
    
    # Currency mappings for standardization
    currency_codes = ['INR', 'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'SGD', 'JPY']
    currency_symbols = ['₹', '$', '€', '£', '¥', '¢']
    
    # Transaction keywords that indicate the primary transaction amount
    # Ordered by priority - more specific keywords first
    transaction_keywords = [
        'total',
        'amount',
        'purchase',
        'spent', 
        'charged',
        'debited',
        'payment of',
        'payment',
        'subscription of',
        'subscription',
        'monthly',
        'billed',
        'transaction',
        'withdrew',
        'withdrawal',
        'transfer',
        'paid',
        'cost',
        'amount due',
        'due',
        'total'
    ]
    
    # Balance keywords to avoid (these typically indicate account balance, not transaction)
    balance_keywords = [
        'avl bal',
        'available balance',
        'balance',
        'bal',
        'remaining',
        'limit',
        'credit limit',
        'ending in'
    ]
    
    def extract_numeric_amount(amount_str: str) -> Optional[float]:
        """Extract numeric value from amount string"""
        try:
            # Remove currency symbols and codes
            cleaned = amount_str
            for symbol in currency_symbols:
                cleaned = cleaned.replace(symbol, '')
            for code in currency_codes:
                cleaned = re.sub(r'\b' + code + r'\b', '', cleaned, flags=re.IGNORECASE)
            
            # Remove spaces and extract number
            cleaned = cleaned.strip()
            
            # Handle comma-separated numbers (e.g., "1,500.00")
            number_match = re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?', cleaned)
            if number_match:
                number_str = number_match.group().replace(',', '')
                return float(number_str)
            
            # Handle simple decimal numbers
            decimal_match = re.search(r'\d+\.\d{1,2}', cleaned)
            if decimal_match:
                return float(decimal_match.group())
            
            # Handle whole numbers
            whole_match = re.search(r'\d+', cleaned)
            if whole_match:
                return float(whole_match.group())
                
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def find_amounts_near_keywords(text: str, keywords: List[str], window: int = 50) -> List[Tuple[float, int, str, int]]:
        """Find amounts near specific keywords with priority scoring"""
        amounts = []
        text_lower = text.lower()
        
        for priority, keyword in enumerate(keywords):
            # Find keyword positions
            keyword_positions = []
            start = 0
            while True:
                pos = text_lower.find(keyword, start)
                if pos == -1:
                    break
                keyword_positions.append(pos)
                start = pos + 1
            
            # For each keyword position, look for nearby amounts
            for pos in keyword_positions:
                # Look in a window around the keyword
                start_pos = max(0, pos - window)
                end_pos = min(len(text), pos + len(keyword) + window)
                window_text = text[start_pos:end_pos]
                
                # Find currency amounts in this window
                currency_patterns = [
                    # Currency code patterns
                    r'\b(?:INR|USD|EUR|GBP|CAD|AUD|SGD|JPY)\s+\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b',
                    # Currency symbol patterns
                    r'[₹$€£¥¢]\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?',
                    # Keyword-amount patterns (e.g., "payment of 1,500")
                    r'(?:' + re.escape(keyword) + r')\s+(?:of\s+)?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?',
                    # Keyword: amount patterns (e.g., "Amount: 25.50", "Total: 123.45")
                    r'(?:' + re.escape(keyword) + r')[:]\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?',
                ]
                
                for pattern in currency_patterns:
                    matches = re.finditer(pattern, window_text, re.IGNORECASE)
                    for match in matches:
                        amount = extract_numeric_amount(match.group())
                        if amount is not None and amount > 0:
                            # Priority score: lower number = higher priority
                            # Distance penalty: closer to keyword = higher priority
                            # Position penalty: earlier in text = higher priority for ties
                            distance = abs(match.start() - (pos - start_pos))
                            position = start_pos + match.start()  # Absolute position in text
                            score = priority * 100 + distance
                            amounts.append((amount, score, keyword, position))
        
        return amounts
    
    def find_standalone_currency_amounts(text: str) -> List[Tuple[float, int, str, int]]:
        """Find standalone currency amounts as fallback"""
        amounts = []
        
        patterns = [
            r'\b(?:INR|USD|EUR|GBP|CAD|AUD|SGD|JPY)\s+\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b',
            r'[₹$€£¥¢]\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?(?!\d)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Skip if this amount is near balance keywords
                context_start = max(0, match.start() - 30)
                context_end = min(len(text), match.end() + 30)
                context = text[context_start:context_end].lower()
                
                # Skip if in balance context
                if any(bal_keyword in context for bal_keyword in balance_keywords):
                    continue
                
                amount = extract_numeric_amount(match.group())
                if amount is not None and amount > 0:
                    # Lower priority for standalone amounts
                    amounts.append((amount, 1000, 'standalone', match.start()))
        
        return amounts
    
    # Step 1: Find amounts near transaction keywords (highest priority)
    transaction_amounts = find_amounts_near_keywords(text, transaction_keywords, window=50)
    
    # Step 2: If no transaction amounts found, look for standalone currency amounts
    if not transaction_amounts:
        transaction_amounts = find_standalone_currency_amounts(text)
    
    # Step 3: Select the best amount based on priority
    if transaction_amounts:
        # Sort by priority score first, then by position (earlier = better for ties)
        transaction_amounts.sort(key=lambda x: (x[1], x[3]))
        best_amount = transaction_amounts[0][0]
        
        # Additional validation: prefer reasonable transaction amounts
        # Avoid extremely large numbers that might be balances or IDs
        reasonable_amounts = [amt for amt, score, keyword, pos in transaction_amounts if 0.01 <= amt <= 100000]
        if reasonable_amounts:
            return reasonable_amounts[0]
        else:
            return best_amount
    
    return None


def test_extract_amount():
    """Comprehensive test suite for the extract_amount function"""
    
    test_cases = [
        # Basic transaction cases
        {
            'input': "Alfamart PURCHASE INR 485.00 on 12-03-2024. Avl bal INR 12,345.67. Trxn ID 1234567890.",
            'expected': 485.00,
            'description': "Transaction amount vs account balance"
        },
        {
            'input': "You spent $29.99 at Amazon.com on Oct 5. Your card ending in 1234 was charged.",
            'expected': 29.99,
            'description': "Spent amount with card number"
        },
        {
            'input': "Acct XXX1234 debited INR 1,500.00 on 05/01/24 for UPI payment to John Doe. Ref No. 987654.",
            'expected': 1500.00,
            'description': "Debited amount with comma separator"
        },
        {
            'input': "Netflix monthly subscription of $15.99 was automatically charged on 2024-10-05.",
            'expected': 15.99,
            'description': "Subscription amount"
        },
        {
            'input': "Payment of INR 2,000.00 to ELECTRICITY BOARD on 12th Mar 2024 successful.",
            'expected': 2000.00,
            'description': "Payment amount with comma"
        },
        
        # Edge cases
        {
            'input': "Your card ending in 4567 charged $125.50. Available balance $1,234.56",
            'expected': 125.50,
            'description': "Transaction vs balance amount"
        },
        {
            'input': "Withdrawal of ₹500.00 from ATM. Transaction ID: 789012345. Balance: ₹15,000.00",
            'expected': 500.00,
            'description': "ATM withdrawal vs balance"
        },
        {
            'input': "Mobile recharge of ₹299 successful. Your number 9876543210 recharged.",
            'expected': 299.00,
            'description': "Recharge amount vs phone number"
        },
        {
            'input': "Grocery purchase $67.89 at Store123. Rewards balance: 1250 points.",
            'expected': 67.89,
            'description': "Purchase amount vs rewards points"
        },
        {
            'input': "Transfer of $1,750.25 to account ending 9876. Fee: $2.50",
            'expected': 1750.25,
            'description': "Transfer amount vs fee (should pick larger amount)"
        },
        
        # Multiple currencies
        {
            'input': "USD 50.00 converted to EUR 42.35. Transaction fee: $1.99",
            'expected': 50.00,
            'description': "Multiple currencies - pick first transaction amount"
        },
        
        # No valid amount
        {
            'input': "Your account ending in 1234 has been activated. Customer service: 1-800-555-0123",
            'expected': None,
            'description': "No transaction amount present"
        },
        
        # Large amounts
        {
            'input': "Wire transfer of $25,000.00 processed. Reference: 1234567890123",
            'expected': 25000.00,
            'description': "Large amount vs reference number"
        },
        
        # Different currency symbols
        {
            'input': "Hotel booking charged €189.50. Confirmation: 98765",
            'expected': 189.50,
            'description': "Euro currency symbol"
        },
        {
            'input': "Online shopping: £75.99 charged to your card 4567",
            'expected': 75.99,
            'description': "British pound symbol"
        }
    ]
    
    print("🧪 Testing Robust Amount Extractor")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        input_text = test_case['input']
        expected = test_case['expected']
        description = test_case['description']
        
        result = extract_amount(input_text)
        
        print(f"\n📝 Test {i}: {description}")
        print(f"Input: {input_text}")
        print(f"Expected: {expected}")
        print(f"Got: {result}")
        
        # Handle floating point comparison
        if expected is None:
            success = result is None
        else:
            success = result is not None and abs(result - expected) < 0.01
        
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


if __name__ == "__main__":
    # Run the test suite
    success = test_extract_amount()
    
    if success:
        print("\n🎉 All tests passed! The extract_amount function is robust and ready.")
    else:
        print("\n⚠️ Some tests failed. Review the function logic.")