#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Live Amount Extraction Testing

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import sys
import os
sys.path.append('/app/backend')

from server import ReceiptOCRProcessor

def test_live_amount_extraction():
    """Test the enhanced amount extraction using the actual OCR processor"""
    
    # Initialize the OCR processor (like in the actual server)
    processor = ReceiptOCRProcessor()
    
    # Test cases
    test_cases = [
        "Alfamart PURCHASE INR 485.00 on 12-03-2024. Avl bal INR 12,345.67. Trxn ID 1234567890.",
        "You spent $29.99 at Amazon.com on Oct 5. Your card ending in 1234 was charged.",
        "Acct XXX1234 debited INR 1,500.00 on 05/01/24 for UPI payment to John Doe. Ref No. 987654.",
        "Netflix monthly subscription of $15.99 was automatically charged on 2024-10-05.",
        "Payment of INR 2,000.00 to ELECTRICITY BOARD on 12th Mar 2024 successful."
    ]
    
    print("🧪 Testing Live Enhanced Amount Extraction")
    print("=" * 60)
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Input: {test_text}")
        
        # Create mock OCR results (simulate what EasyOCR would return)
        mock_ocr_results = [
            ([[0, 0], [100, 0], [100, 20], [0, 20]], test_text, 0.95)
        ]
        
        # Use the actual parse_receipt_text method from the server
        parsed_data = processor.parse_receipt_text(test_text, mock_ocr_results)
        
        print(f"Extracted merchant: {parsed_data.get('merchant_name', 'None')}")
        print(f"Extracted amount: {parsed_data.get('total_amount', 'None')}")
        print(f"Confidence score: {parsed_data.get('confidence_score', 0):.2f}")
        
        if parsed_data.get('total_amount'):
            print("✅ SUCCESS - Amount extracted")
        else:
            print("❌ FAILED - No amount extracted")

if __name__ == "__main__":
    test_live_amount_extraction()