#!/usr/bin/env python3
"""
Test Upload with Real Images
"""

import requests
import time

def test_real_image_upload():
    """Test with real receipt images"""
    
    BASE_URL = "http://localhost:8001/api"
    
    print("🧪 Testing Real Image Upload")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Starbucks Receipt',
            'file': '/tmp/starbucks_receipt.jpg',
            'expected_category': 'Dining'
        },
        {
            'name': 'Walmart Grocery Receipt', 
            'file': '/tmp/walmart_receipt.jpg',
            'expected_category': 'Groceries'
        }
    ]
    
    receipt_ids = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Testing {test['name']}")
        
        try:
            # Upload the receipt
            with open(test['file'], 'rb') as f:
                files = {'file': (test['file'].split('/')[-1], f, 'image/jpeg')}
                data = {'category': 'Auto-Detect'}
                
                response = requests.post(f"{BASE_URL}/receipts/upload", files=files, data=data)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                receipt_id = result.get('id')
                receipt_ids.append(receipt_id)
                
                print(f"   ✅ Upload successful!")
                print(f"   Receipt ID: {receipt_id}")
                print(f"   Processing Status: {result.get('processing_status', 'N/A')}")
                
                # Wait a moment for processing
                print("   ⏳ Waiting for OCR processing...")
                time.sleep(12)  # Allow time for processing
                
                # Check the processed result
                get_response = requests.get(f"{BASE_URL}/receipts/{receipt_id}")
                if get_response.status_code == 200:
                    processed_result = get_response.json()
                    
                    print(f"   📊 Processing Results:")
                    print(f"      Status: {processed_result.get('processing_status', 'N/A')}")
                    print(f"      Merchant: {processed_result.get('merchant_name', 'N/A')}")
                    print(f"      Amount: {processed_result.get('total_amount', 'N/A')}")
                    print(f"      Date: {processed_result.get('receipt_date', 'N/A')}")
                    print(f"      Category: {processed_result.get('category', 'N/A')}")
                    print(f"      Confidence: {processed_result.get('category_confidence', 'N/A')}")
                    print(f"      Method: {processed_result.get('categorization_method', 'N/A')}")
                    
                    # Check if category matches expectation
                    if processed_result.get('category') == test['expected_category']:
                        print(f"   ✅ Category prediction correct: {test['expected_category']}")
                    elif processed_result.get('processing_status') == 'completed':
                        print(f"   ⚠️ Category prediction different: got {processed_result.get('category')}, expected {test['expected_category']}")
                    else:
                        print(f"   ⚠️ Processing not completed successfully")
                        
                    # Show items if available
                    items = processed_result.get('items', [])
                    if items:
                        print(f"   📋 Items found: {len(items)}")
                        for item in items[:3]:  # Show first 3 items
                            print(f"      - {item.get('description', 'N/A')}: {item.get('amount', 'N/A')}")
                else:
                    print(f"   ❌ Could not fetch processed result")
                
            else:
                print(f"   ❌ Upload failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    return receipt_ids

def test_pdf_upload():
    """Test PDF upload functionality"""
    print(f"\n3️⃣ Testing PDF Upload")
    
    BASE_URL = "http://localhost:8001/api"
    
    try:
        # Create a simple PDF-like content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f 
0000000010 00000 n 
0000000079 00000 n 
0000000173 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
301
%%EOF"""
        
        # Write PDF to temp file
        pdf_path = "/tmp/test_receipt.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        
        # Upload the PDF
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test_receipt.pdf', f, 'application/pdf')}
            data = {'category': 'Auto-Detect'}
            
            response = requests.post(f"{BASE_URL}/receipts/upload", files=files, data=data)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ PDF upload successful!")
            print(f"   Receipt ID: {result.get('id', 'N/A')}")
            print(f"   Processing Status: {result.get('processing_status', 'N/A')}")
            return result.get('id')
        else:
            print(f"   ❌ PDF upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ PDF upload error: {str(e)}")
        return None

def cleanup_receipts(receipt_ids):
    """Clean up test receipts"""
    BASE_URL = "http://localhost:8001/api"
    
    print(f"\n🧹 Cleaning up {len(receipt_ids)} test receipts...")
    for receipt_id in receipt_ids:
        if receipt_id:
            try:
                response = requests.delete(f"{BASE_URL}/receipts/{receipt_id}")
                if response.status_code == 200:
                    print(f"   ✅ Cleaned up {receipt_id}")
            except:
                pass

if __name__ == "__main__":
    receipt_ids = []
    
    # Test image uploads
    image_receipt_ids = test_real_image_upload()
    receipt_ids.extend(image_receipt_ids)
    
    # Test PDF upload
    pdf_receipt_id = test_pdf_upload()
    if pdf_receipt_id:
        receipt_ids.append(pdf_receipt_id)
    
    # Clean up
    cleanup_receipts(receipt_ids)
    
    print("\n" + "=" * 50)
    print("🎉 Comprehensive upload testing completed!")
    print("Both image and PDF upload functionality has been tested.")