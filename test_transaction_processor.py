#!/usr/bin/env python3
"""
Focused test for Master Transaction Processor Integration
"""

import requests
import json
import io
from PIL import Image, ImageDraw, ImageFont

def create_test_receipt(merchant_type="starbucks"):
    """Create test receipt image"""
    try:
        img = Image.new('RGB', (400, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        if merchant_type == "starbucks":
            receipt_text = [
                "STARBUCKS COFFEE",
                "Store #12345",
                "123 Coffee Street",
                "Date: 12/15/2024",
                "Time: 08:30 AM",
                "",
                "Grande Latte      $5.25",
                "Blueberry Muffin  $3.50",
                "",
                "Subtotal          $8.75",
                "Tax               $0.70",
                "TOTAL            $9.45"
            ]
        elif merchant_type == "walmart":
            receipt_text = [
                "WALMART SUPERCENTER",
                "Store #4567",
                "456 Market Ave",
                "Date: 12/15/2024",
                "",
                "Bananas 2lb       $2.98",
                "Bread Loaf        $1.50",
                "Milk Gallon       $3.25",
                "Eggs Dozen        $2.99",
                "",
                "Subtotal         $10.72",
                "Tax               $0.86",
                "TOTAL           $11.58"
            ]
        
        y_position = 50
        for line in receipt_text:
            draw.text((50, y_position), line, fill='black', font=font)
            y_position += 25
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes
        
    except ImportError:
        # Fallback text version
        if merchant_type == "starbucks":
            text_content = "STARBUCKS COFFEE\nDate: 12/15/2024\nGrande Latte $5.25\nTOTAL $9.45"
        else:
            text_content = "WALMART SUPERCENTER\nDate: 12/15/2024\nBananas $2.98\nTOTAL $11.58"
        
        return io.BytesIO(text_content.encode())

def test_transaction_processor():
    """Test Master Transaction Processor Integration"""
    base_url = "https://expensify-ai.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔥 Testing Master Transaction Processor Integration")
    print("=" * 60)
    
    # Test 1: Starbucks (Dining Category)
    print("\n1. Testing Starbucks Receipt (Expected: Dining Category)")
    try:
        test_image = create_test_receipt("starbucks")
        
        files = {
            'file': ('starbucks_test.png', test_image, 'image/png')
        }
        data = {'category': 'Auto-Detect'}
        
        response = requests.post(f"{api_url}/receipts/upload", data=data, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS - Status: {response.status_code}")
            print(f"   Merchant: {result.get('merchant_name', 'N/A')}")
            print(f"   Amount: {result.get('total_amount', 'N/A')}")
            print(f"   Category: {result.get('category', 'N/A')}")
            print(f"   Date: {result.get('receipt_date', 'N/A')}")
            print(f"   Processing Status: {result.get('processing_status', 'N/A')}")
            print(f"   Confidence: {result.get('confidence_score', 'N/A')}")
            
            # Check if transaction processor worked
            if result.get('merchant_name') and result.get('total_amount') and result.get('category'):
                print("   🎉 Transaction Processor Integration: WORKING")
            else:
                print("   ⚠️ Transaction Processor Integration: PARTIAL")
                
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 2: Walmart (Groceries Category)
    print("\n2. Testing Walmart Receipt (Expected: Groceries Category)")
    try:
        test_image = create_test_receipt("walmart")
        
        files = {
            'file': ('walmart_test.png', test_image, 'image/png')
        }
        data = {'category': 'Auto-Detect'}
        
        response = requests.post(f"{api_url}/receipts/upload", data=data, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS - Status: {response.status_code}")
            print(f"   Merchant: {result.get('merchant_name', 'N/A')}")
            print(f"   Amount: {result.get('total_amount', 'N/A')}")
            print(f"   Category: {result.get('category', 'N/A')}")
            print(f"   Date: {result.get('receipt_date', 'N/A')}")
            print(f"   Processing Status: {result.get('processing_status', 'N/A')}")
            print(f"   Confidence: {result.get('confidence_score', 'N/A')}")
            
            # Check if transaction processor worked
            if result.get('merchant_name') and result.get('total_amount') and result.get('category'):
                print("   🎉 Transaction Processor Integration: WORKING")
            else:
                print("   ⚠️ Transaction Processor Integration: PARTIAL")
                
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Master Transaction Processor Integration Test Complete")

if __name__ == "__main__":
    test_transaction_processor()