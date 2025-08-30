#!/usr/bin/env python3
"""
Test Upload Functionality Fix
"""

import requests
import os
from pathlib import Path

def test_upload_functionality():
    """Test receipt upload functionality"""
    
    BASE_URL = "http://localhost:8001/api"
    
    print("🧪 Testing Upload Functionality Fix")
    print("=" * 50)
    
    # Test 1: Image Upload
    print("\n1️⃣ Testing Image Upload")
    try:
        # Create test image content (simple text file as image)
        test_content = """STARBUCKS COFFEE
123 Main Street
Seattle, WA 98101

Date: 12/15/2024
Time: 07:23 AM

Latte Grande     $5.25
Croissant        $3.50
Tax              $0.70

TOTAL           $9.45

Card ending 1234
Thank you!"""
        
        # Create a test image file
        test_file_path = "/tmp/test_receipt.jpg"
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        # Upload the file
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_receipt.jpg', f, 'image/jpeg')}
            data = {'category': 'Auto-Detect'}
            
            response = requests.post(f"{BASE_URL}/receipts/upload", files=files, data=data)
            
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Upload successful!")
            print(f"   Receipt ID: {result.get('id', 'N/A')}")
            print(f"   Merchant: {result.get('merchant_name', 'N/A')}")
            print(f"   Amount: {result.get('total_amount', 'N/A')}")
            print(f"   Category: {result.get('category', 'N/A')}")
            print(f"   Status: {result.get('processing_status', 'N/A')}")
            
            # Store receipt ID for cleanup
            receipt_id = result.get('id')
            return receipt_id
        else:
            print(f"   ❌ Upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

    # Test 2: PDF Upload
    print("\n2️⃣ Testing PDF Upload")
    try:
        # Create test PDF content (text file with .pdf extension for testing)
        test_pdf_content = """WALMART SUPERCENTER
SAVE MONEY. LIVE BETTER.

Date: 12/16/2024

Milk Organic 1 Gal    $4.98
Bread Whole Wheat     $2.49
Eggs Dozen           $3.25
Apples 3 lbs         $4.99

SUBTOTAL            $15.71
TAX                 $1.26
TOTAL              $16.97

Visa ending 4567
Thank you for shopping!"""
        
        test_pdf_path = "/tmp/test_receipt.pdf"
        with open(test_pdf_path, 'w') as f:
            f.write(test_pdf_content)
        
        # Upload the PDF
        with open(test_pdf_path, 'rb') as f:
            files = {'file': ('test_receipt.pdf', f, 'application/pdf')}
            data = {'category': 'Auto-Detect'}
            
            response = requests.post(f"{BASE_URL}/receipts/upload", files=files, data=data)
            
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ PDF upload successful!")
            print(f"   Receipt ID: {result.get('id', 'N/A')}")
            print(f"   Merchant: {result.get('merchant_name', 'N/A')}")
            print(f"   Amount: {result.get('total_amount', 'N/A')}")
            print(f"   Category: {result.get('category', 'N/A')}")
            print(f"   Status: {result.get('processing_status', 'N/A')}")
            
            return result.get('id')
        else:
            print(f"   ❌ PDF upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def cleanup_test_receipts(receipt_ids):
    """Clean up test receipts"""
    BASE_URL = "http://localhost:8001/api"
    
    print("\n🧹 Cleaning up test receipts...")
    for receipt_id in receipt_ids:
        if receipt_id:
            try:
                response = requests.delete(f"{BASE_URL}/receipts/{receipt_id}")
                if response.status_code == 200:
                    print(f"   ✅ Cleaned up receipt {receipt_id}")
                else:
                    print(f"   ⚠️ Could not clean up receipt {receipt_id}")
            except:
                pass

if __name__ == "__main__":
    receipt_ids = []
    
    # Test image upload
    receipt_id = test_upload_functionality()
    if receipt_id:
        receipt_ids.append(receipt_id)
    
    # Clean up
    cleanup_test_receipts(receipt_ids)
    
    print("\n" + "=" * 50)
    print("🎉 Upload test completed!")