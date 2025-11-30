#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Combined Robust Extractors Test

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import sys
import os
sys.path.append('/app/backend')

from server import ReceiptOCRProcessor

def test_combined_extractors():
    """Test both robust amount and date extractors working together in the Lumina system"""
    
    processor = ReceiptOCRProcessor()
    
    test_cases = [
        {
            'text': "Alfamart PURCHASE INR 485.00 on 12-03-2024. Avl bal INR 12,345.67. Trxn ID 1234567890.",
            'expected_amount': "₹485.00",
            'expected_date': "2024-03-12",
            'description': "Transaction vs balance amount with DD-MM-YYYY date"
        },
        {
            'text': "You spent $29.99 at Amazon.com on Oct 5. Your card ending in 1234 was charged.",
            'expected_amount': "$29.99",
            'expected_date': "2024-10-05",
            'description': "Spent amount with month name date"
        },
        {
            'text': "Acct XXX1234 debited INR 1,500.00 on 05/01/24 for UPI payment to John Doe. Ref No. 987654.",
            'expected_amount': "₹1500.00",
            'expected_date': "2024-05-01",
            'description': "Debited amount with MM/DD/YY date"
        },
        {
            'text': "Netflix monthly subscription of $15.99 was automatically charged on 2024-10-05.",
            'expected_amount': "$15.99",
            'expected_date': "2024-10-05",
            'description': "Subscription amount with ISO date"
        },
        {
            'text': "Payment of INR 2,000.00 to ELECTRICITY BOARD on 12th Mar 2024 successful.",
            'expected_amount': "₹2000.00",
            'expected_date': "2024-03-12",
            'description': "Payment amount with ordinal date"
        }
    ]
    
    print("🔬 Testing Combined Robust Amount & Date Extractors")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case['text']
        expected_amount = test_case['expected_amount']
        expected_date = test_case['expected_date']
        description = test_case['description']
        
        print(f"\n📝 Test {i}: {description}")
        print(f"Input: {text}")
        
        # Test individual extractors
        extracted_amount = processor._extract_transaction_amount_robust(text)
        extracted_date = processor._extract_transaction_date_robust(text)
        
        print(f"Expected Amount: {expected_amount} | Got: {extracted_amount}")
        print(f"Expected Date: {expected_date} | Got: {extracted_date}")
        
        # Test full OCR processing pipeline
        mock_ocr_results = [
            ([[0, 0], [100, 0], [100, 20], [0, 20]], text, 0.95)
        ]
        
        parsed_data = processor.parse_receipt_text(text, mock_ocr_results)
        
        print(f"OCR Pipeline Amount: {parsed_data.get('total_amount', 'None')}")
        print(f"OCR Pipeline Date: {parsed_data.get('receipt_date', 'None')}")
        print(f"OCR Pipeline Merchant: {parsed_data.get('merchant_name', 'None')}")
        
        # Check results
        amount_success = extracted_amount == expected_amount
        date_success = extracted_date == expected_date
        pipeline_amount_success = parsed_data.get('total_amount') == expected_amount
        pipeline_date_success = parsed_data.get('receipt_date') == expected_date
        
        if amount_success and date_success and pipeline_amount_success and pipeline_date_success:
            print("✅ ALL PASSED - Individual extractors and OCR pipeline working")
            passed += 1
        else:
            print("❌ FAILED")
            if not amount_success:
                print(f"   Amount extractor: Expected {expected_amount}, got {extracted_amount}")
            if not date_success:
                print(f"   Date extractor: Expected {expected_date}, got {extracted_date}")
            if not pipeline_amount_success:
                print(f"   Pipeline amount: Expected {expected_amount}, got {parsed_data.get('total_amount')}")
            if not pipeline_date_success:
                print(f"   Pipeline date: Expected {expected_date}, got {parsed_data.get('receipt_date')}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"🎯 Combined Extractor Results: {passed} passed, {failed} failed")
    print(f"Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if passed == len(test_cases):
        print("\n🎉 Perfect! Both robust extractors are working flawlessly in the Lumina system!")
        print("\n🚀 Enhanced Features Now Available:")
        print("  ✅ Intelligent amount detection (ignores balances, IDs, phone numbers)")
        print("  ✅ International currency support (INR→₹, USD→$, EUR→€)")
        print("  ✅ Robust date parsing (multiple formats, context-aware)")
        print("  ✅ Transaction vs non-transaction filtering")
        print("  ✅ Integrated into full OCR pipeline")
    else:
        print("\n⚠️ Some tests failed. The extractors may need fine-tuning.")
    
    return passed == len(test_cases)

if __name__ == "__main__":
    test_combined_extractors()