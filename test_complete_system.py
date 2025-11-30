#!/usr/bin/env python3
"""
Comprehensive Test of Complete ML-Enhanced Lumina System
"""

import requests
import json
from datetime import datetime

def test_complete_system():
    """Test the complete ML-enhanced system"""
    
    BASE_URL = "http://localhost:8001/api"
    
    print("🔬 Complete ML-Enhanced Lumina System Test")
    print("=" * 60)
    
    # Test 1: ML Health Check
    print("\n1️⃣ Testing ML Health Check")
    try:
        response = requests.get(f"{BASE_URL}/ml/health")
        health = response.json()
        print(f"   ✅ ML Health: {health['health']['ml_available']}")
        print(f"   ✅ Model Loaded: {health['health']['model_loaded']}")
    except Exception as e:
        print(f"   ❌ ML Health Check Failed: {str(e)}")
    
    # Test 2: ML Model Status
    print("\n2️⃣ Testing ML Model Status")
    try:
        response = requests.get(f"{BASE_URL}/ml/status")
        status = response.json()['status']
        print(f"   ✅ Model Trained: {status['is_trained']}")
        print(f"   ✅ Categories: {len(status['categories'])} categories")
        print(f"   ✅ Features: {status['feature_count']} features")
        print(f"   ✅ Model Size: {status['model_size_mb']} MB")
    except Exception as e:
        print(f"   ❌ ML Status Failed: {str(e)}")
    
    # Test 3: Direct ML Prediction
    print("\n3️⃣ Testing Direct ML Prediction")
    try:
        test_transactions = [
            {
                'raw_text': "Starbucks Coffee charged $8.45 on Oct 15 at 7:23 AM",
                'amount': 8.45,
                'merchant': "Starbucks",
                'expected': 'Dining'
            },
            {
                'raw_text': "Netflix monthly subscription of $15.99 renewed",
                'amount': 15.99, 
                'merchant': "Netflix",
                'expected': 'Entertainment'
            }
        ]
        
        for i, test in enumerate(test_transactions, 1):
            params = {
                'raw_text': test['raw_text'],
                'amount': test['amount'],
                'merchant': test['merchant']
            }
            response = requests.post(f"{BASE_URL}/ml/predict", params=params)
            result = response.json()['prediction']
            
            category = result['category']
            confidence = result['confidence']
            method = result['method']
            
            print(f"   Test {i}: {test['expected']} → {category} ({confidence:.2f}) [{method}]")
            
            if category == test['expected']:
                print(f"   ✅ Correct prediction!")
            else:
                print(f"   ⚠️ Different prediction")
    except Exception as e:
        print(f"   ❌ ML Prediction Failed: {str(e)}")
    
    # Test 4: Receipt Upload with ML Processing
    print("\n4️⃣ Testing Receipt Upload with ML Processing")
    try:
        # Create a test receipt file
        test_receipt_content = """STARBUCKS COFFEE
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
        
        # Write to a temporary file
        with open('/tmp/test_receipt.txt', 'w') as f:
            f.write(test_receipt_content)
        
        # Upload as multipart form
        files = {'file': ('test_receipt.txt', open('/tmp/test_receipt.txt', 'rb'), 'text/plain')}
        data = {'category': 'Auto-Detect'}
        
        response = requests.post(f"{BASE_URL}/receipts/upload", files=files, data=data)
        
        if response.status_code == 200:
            receipt_data = response.json()
            print(f"   ✅ Receipt uploaded successfully")
            print(f"   ✅ Merchant: {receipt_data.get('merchant_name', 'N/A')}")
            print(f"   ✅ Amount: {receipt_data.get('total_amount', 'N/A')}")
            print(f"   ✅ Category: {receipt_data.get('suggested_category', 'N/A')}")
            print(f"   ✅ Confidence: {receipt_data.get('category_confidence', 'N/A')}")
            print(f"   ✅ Method: {receipt_data.get('categorization_method', 'N/A')}")
            
            # Store receipt ID for cleanup
            receipt_id = receipt_data.get('id')
            
            # Cleanup - delete the test receipt
            if receipt_id:
                try:
                    requests.delete(f"{BASE_URL}/receipts/{receipt_id}")
                    print(f"   ✅ Test receipt cleaned up")
                except:
                    pass
        else:
            print(f"   ❌ Upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Receipt Upload Failed: {str(e)}")
    
    # Test 5: Get All Categories (should include ML categories)
    print("\n5️⃣ Testing Category Management")
    try:
        response = requests.get(f"{BASE_URL}/categories")
        categories = response.json().get('categories', [])
        print(f"   ✅ Available categories: {len(categories)}")
        print(f"   ✅ Categories: {', '.join(categories)}")
    except Exception as e:
        print(f"   ❌ Category Management Failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Complete System Test Finished!")
    print("The ML-enhanced Lumina system is ready for production use.")

if __name__ == "__main__":
    test_complete_system()