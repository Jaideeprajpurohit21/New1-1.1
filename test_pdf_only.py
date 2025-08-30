#!/usr/bin/env python3
"""
Test PDF Upload Only
"""

import requests
import time

def test_pdf_upload():
    """Test PDF upload with poppler installed"""
    
    BASE_URL = "http://localhost:8001/api"
    
    print("📺 Testing Netflix PDF Receipt")
    print("=" * 40)
    
    try:
        # Upload the PDF
        with open('/tmp/netflix_receipt.pdf', 'rb') as f:
            files = {'file': ('netflix_receipt.pdf', f, 'application/pdf')}
            data = {'category': 'Auto-Detect'}
            
            response = requests.post(f"{BASE_URL}/receipts/upload", files=files, data=data)
        
        print(f"Upload Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            receipt_id = result.get('id')
            
            print(f"✅ PDF Upload Successful!")
            print(f"Receipt ID: {receipt_id}")
            print(f"Processing Status: {result.get('processing_status', 'N/A')}")
            
            # Wait for processing
            print("⏳ Waiting for PDF processing...")
            time.sleep(15)
            
            # Check result
            get_response = requests.get(f"{BASE_URL}/receipts/{receipt_id}")
            if get_response.status_code == 200:
                processed = get_response.json()
                
                print("\n📊 PDF PROCESSING RESULTS:")
                print(f"   Status: {processed.get('processing_status', 'N/A')}")
                print(f"   Merchant: {processed.get('merchant_name', 'N/A')}")
                print(f"   Amount: {processed.get('total_amount', 'N/A')}")
                print(f"   Category: {processed.get('category', 'N/A')}")
                print(f"   Confidence: {processed.get('category_confidence', 'N/A')}")
                print(f"   Method: {processed.get('categorization_method', 'N/A')}")
                
                # Clean up
                requests.delete(f"{BASE_URL}/receipts/{receipt_id}")
                print(f"\n✅ Test receipt cleaned up")
                
                if processed.get('processing_status') == 'completed':
                    print("🎉 PDF processing is now working!")
                    return True
                else:
                    print("⚠️ PDF processing still has issues")
                    return False
            else:
                print("❌ Could not fetch result")
                return False
        else:
            print(f"❌ Upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_pdf_upload()
    if success:
        print("\n🎉 PDF upload functionality is now PERFECT!")
    else:
        print("\n⚠️ PDF upload needs more work")