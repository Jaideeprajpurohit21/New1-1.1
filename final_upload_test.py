#!/usr/bin/env python3
"""
Final Comprehensive Upload Test
"""

import requests
import time

def test_final_upload():
    """Final comprehensive test of upload functionality"""
    
    BASE_URL = "http://localhost:8001/api"
    
    print("🎯 FINAL COMPREHENSIVE UPLOAD TEST")
    print("=" * 60)
    
    test_cases = [
        {
            'name': '☕ Starbucks Coffee Receipt (Image)',
            'file': '/tmp/starbucks_receipt.jpg',
            'mime_type': 'image/jpeg',
            'expected_category': 'Dining',
            'expected_merchant': 'Starbucks'
        },
        {
            'name': '🛒 Walmart Grocery Receipt (Image)',
            'file': '/tmp/walmart_receipt.jpg', 
            'mime_type': 'image/jpeg',
            'expected_category': 'Groceries',
            'expected_merchant': 'Walmart'
        },
        {
            'name': '📺 Netflix Subscription (PDF)',
            'file': '/tmp/netflix_receipt.pdf',
            'mime_type': 'application/pdf', 
            'expected_category': 'Entertainment',
            'expected_merchant': 'Netflix'
        }
    ]
    
    results = []
    receipt_ids = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Testing: {test['name']}")
        
        try:
            # Upload the receipt
            with open(test['file'], 'rb') as f:
                files = {'file': (test['file'].split('/')[-1], f, test['mime_type'])}
                data = {'category': 'Auto-Detect'}
                
                response = requests.post(f"{BASE_URL}/receipts/upload", files=files, data=data)
            
            print(f"   📤 Upload Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                receipt_id = result.get('id')
                receipt_ids.append(receipt_id)
                
                print(f"   ✅ Upload Successful!")
                print(f"   📋 Receipt ID: {receipt_id[:8]}...")
                print(f"   🔄 Processing Status: {result.get('processing_status', 'N/A')}")
                
                # Wait for processing
                print(f"   ⏳ Waiting for ML processing...")
                time.sleep(15)  # Extended wait for ML processing
                
                # Get processed result
                get_response = requests.get(f"{BASE_URL}/receipts/{receipt_id}")
                if get_response.status_code == 200:
                    processed = get_response.json()
                    
                    print(f"\n   📊 PROCESSING RESULTS:")
                    print(f"      Status: {processed.get('processing_status', 'N/A')}")
                    print(f"      Merchant: {processed.get('merchant_name', 'N/A')}")
                    print(f"      Amount: {processed.get('total_amount', 'N/A')}")
                    print(f"      Date: {processed.get('receipt_date', 'N/A')}")
                    print(f"      Category: {processed.get('category', 'N/A')}")
                    print(f"      ML Confidence: {processed.get('category_confidence', 'N/A')}")
                    print(f"      Method: {processed.get('categorization_method', 'N/A')}")
                    
                    # Evaluate results
                    success_metrics = {
                        'upload': True,
                        'processing': processed.get('processing_status') == 'completed',
                        'merchant': bool(processed.get('merchant_name')),
                        'category_correct': processed.get('category') == test['expected_category'],
                        'ml_confidence': processed.get('category_confidence', 0) > 0,
                        'method_tracked': bool(processed.get('categorization_method'))
                    }
                    
                    print(f"\n   🎯 SUCCESS METRICS:")
                    for metric, status in success_metrics.items():
                        emoji = "✅" if status else "❌"
                        print(f"      {emoji} {metric.replace('_', ' ').title()}: {status}")
                    
                    # Calculate success rate
                    success_rate = sum(success_metrics.values()) / len(success_metrics)
                    print(f"   📈 Overall Success Rate: {success_rate:.1%}")
                    
                    results.append({
                        'name': test['name'],
                        'success_rate': success_rate,
                        'metrics': success_metrics,
                        'processed': processed
                    })
                else:
                    print(f"   ❌ Could not fetch processed result")
                    results.append({'name': test['name'], 'success_rate': 0.0})
                
            else:
                print(f"   ❌ Upload Failed: {response.text}")
                results.append({'name': test['name'], 'success_rate': 0.0})
                
        except Exception as e:
            print(f"   💥 Error: {str(e)}")
            results.append({'name': test['name'], 'success_rate': 0.0})
    
    # Overall results
    print(f"\n" + "=" * 60)
    print(f"📈 OVERALL SYSTEM PERFORMANCE")
    print(f"=" * 60)
    
    total_success = sum(r['success_rate'] for r in results) / len(results)
    
    for result in results:
        rate = result['success_rate']
        emoji = "🎉" if rate >= 0.8 else "⚠️" if rate >= 0.6 else "❌"
        print(f"   {emoji} {result['name']}: {rate:.1%}")
    
    print(f"\n🏆 TOTAL SYSTEM SUCCESS RATE: {total_success:.1%}")
    
    if total_success >= 0.8:
        print(f"🎉 EXCELLENT! Upload system is working perfectly!")
    elif total_success >= 0.6:
        print(f"👍 GOOD! Upload system is working well with minor issues.")
    else:
        print(f"⚠️ NEEDS IMPROVEMENT! Upload system has significant issues.")
    
    # Clean up
    print(f"\n🧹 Cleaning up {len(receipt_ids)} test receipts...")
    for receipt_id in receipt_ids:
        if receipt_id:
            try:
                requests.delete(f"{BASE_URL}/receipts/{receipt_id}")
            except:
                pass
    
    return total_success

if __name__ == "__main__":
    success_rate = test_final_upload()
    print(f"\n🎯 Final System Grade: {success_rate:.1%}")
    
    if success_rate >= 0.85:
        print("🌟 LUMINA UPLOAD SYSTEM: PERFECT!")
    elif success_rate >= 0.70:
        print("✅ LUMINA UPLOAD SYSTEM: EXCELLENT!")
    elif success_rate >= 0.60:
        print("👍 LUMINA UPLOAD SYSTEM: GOOD!")
    else:
        print("⚠️ LUMINA UPLOAD SYSTEM: NEEDS FIXES!")