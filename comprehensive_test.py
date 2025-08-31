#!/usr/bin/env python3
"""
LUMINA - FINAL COMPREHENSIVE TEST
Testing all critical functionality for production readiness
"""

import requests
import json
import io
import tempfile
import time
from datetime import datetime
from pathlib import Path

class LuminaComprehensiveTest:
    def __init__(self):
        self.base_url = "https://expense-ai-5.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.receipt_ids = []
        
    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
        return success

    def create_starbucks_receipt(self):
        """Create Starbucks receipt for dining category test"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (400, 600), color='white')
            draw = ImageDraw.Draw(img)
            
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
            
            y_position = 50
            for line in receipt_text:
                draw.text((50, y_position), line, fill='black')
                y_position += 25
            
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes
            
        except ImportError:
            text_content = "STARBUCKS COFFEE\nDate: 12/15/2024\nGrande Latte $5.25\nBlueberry Muffin $3.50\nTOTAL $9.45"
            return io.BytesIO(text_content.encode())

    def create_walmart_receipt(self):
        """Create Walmart receipt for groceries category test"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (400, 600), color='white')
            draw = ImageDraw.Draw(img)
            
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
                draw.text((50, y_position), line, fill='black')
                y_position += 25
            
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes
            
        except ImportError:
            text_content = "WALMART SUPERCENTER\nDate: 12/15/2024\nBananas $2.98\nBread $1.50\nMilk $3.25\nTOTAL $11.58"
            return io.BytesIO(text_content.encode())

    def create_netflix_pdf(self):
        """Create Netflix PDF receipt for entertainment category test"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            
            c.drawString(100, 750, "NETFLIX SUBSCRIPTION")
            c.drawString(100, 730, "Monthly Billing Statement")
            c.drawString(100, 710, "Date: 12/15/2024")
            c.drawString(100, 690, "")
            c.drawString(100, 670, "Standard Plan        $15.99")
            c.drawString(100, 650, "")
            c.drawString(100, 630, "Next Billing: 01/15/2025")
            c.drawString(100, 610, "TOTAL              $15.99")
            
            c.save()
            pdf_buffer.seek(0)
            return pdf_buffer
            
        except ImportError:
            text_content = "NETFLIX SUBSCRIPTION\nDate: 12/15/2024\nStandard Plan $15.99\nTOTAL $15.99"
            return io.BytesIO(text_content.encode())

    def test_ml_endpoints(self):
        """Test all ML API endpoints"""
        print("\n🤖 TESTING ML API ENDPOINTS")
        
        # Test ML Health
        try:
            response = requests.get(f"{self.api_url}/ml/health", timeout=10)
            health_data = response.json()
            success = (response.status_code == 200 and 
                      health_data.get('success') and 
                      health_data.get('health', {}).get('model_loaded'))
            self.log_test("ML Health Check", success, 
                         f"Model loaded: {health_data.get('health', {}).get('model_loaded')}")
        except Exception as e:
            self.log_test("ML Health Check", False, str(e))
        
        # Test ML Status
        try:
            response = requests.get(f"{self.api_url}/ml/status", timeout=10)
            status_data = response.json()
            success = (response.status_code == 200 and 
                      status_data.get('success') and 
                      status_data.get('status', {}).get('is_trained'))
            
            if success:
                status = status_data.get('status', {})
                categories = status.get('categories', [])
                feature_count = status.get('feature_count', 0)
                test_accuracy = status.get('training_results', {}).get('test_accuracy', 0)
                
                self.log_test("ML Status Check", success, 
                             f"Categories: {len(categories)}, Features: {feature_count}, Accuracy: {test_accuracy:.1%}")
            else:
                self.log_test("ML Status Check", False, "Model not trained")
        except Exception as e:
            self.log_test("ML Status Check", False, str(e))
        
        # Test ML Prediction
        try:
            response = requests.post(f"{self.api_url}/ml/predict", 
                                   json={
                                       "raw_text": "Starbucks coffee purchase $8.45",
                                       "amount": 8.45,
                                       "merchant": "Starbucks"
                                   }, timeout=10)
            pred_data = response.json()
            success = (response.status_code == 200 and 
                      pred_data.get('success') and 
                      pred_data.get('prediction', {}).get('category'))
            
            if success:
                prediction = pred_data.get('prediction', {})
                category = prediction.get('category')
                confidence = prediction.get('confidence', 0)
                self.log_test("ML Direct Prediction", success, 
                             f"Category: {category}, Confidence: {confidence:.3f}")
            else:
                self.log_test("ML Direct Prediction", False, "No prediction returned")
        except Exception as e:
            self.log_test("ML Direct Prediction", False, str(e))

    def test_upload_starbucks_receipt(self):
        """Test Starbucks receipt upload and ML categorization"""
        print("\n☕ TESTING STARBUCKS RECEIPT (DINING CATEGORY)")
        
        try:
            test_image = self.create_starbucks_receipt()
            
            files = {'file': ('starbucks_receipt.png', test_image, 'image/png')}
            data = {'category': 'Auto-Detect'}
            
            response = requests.post(f"{self.api_url}/receipts/upload", 
                                   data=data, files=files, timeout=30)
            
            if response.status_code == 200:
                receipt_data = response.json()
                self.receipt_ids.append(receipt_data.get('id'))
                
                # Check all required fields
                category = receipt_data.get('category', '')
                merchant = receipt_data.get('merchant_name', '')
                amount = receipt_data.get('total_amount', '')
                status = receipt_data.get('processing_status', '')
                confidence = receipt_data.get('category_confidence', 0)
                method = receipt_data.get('categorization_method', '')
                
                success = (status == 'completed' and 
                          'starbucks' in merchant.lower() if merchant else False)
                
                details = f"Category: {category}, Merchant: {merchant}, Amount: {amount}, Status: {status}, ML Confidence: {confidence}, Method: {method}"
                self.log_test("Starbucks Receipt Upload & Processing", success, details)
                
                # Check if ML categorization worked
                dining_categories = ['dining', 'meals', 'entertainment']
                ml_success = (any(cat in category.lower() for cat in dining_categories) and 
                             confidence > 0.3 and method == 'advanced_ml')
                self.log_test("Starbucks ML Category Prediction", ml_success, 
                             f"Expected: Dining, Got: {category} (confidence: {confidence})")
                
                return success
            else:
                self.log_test("Starbucks Receipt Upload", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Starbucks Receipt Upload", False, str(e))
            return False

    def test_upload_walmart_receipt(self):
        """Test Walmart receipt upload and ML categorization"""
        print("\n🛒 TESTING WALMART RECEIPT (GROCERIES CATEGORY)")
        
        try:
            test_image = self.create_walmart_receipt()
            
            files = {'file': ('walmart_receipt.png', test_image, 'image/png')}
            data = {'category': 'Auto-Detect'}
            
            response = requests.post(f"{self.api_url}/receipts/upload", 
                                   data=data, files=files, timeout=30)
            
            if response.status_code == 200:
                receipt_data = response.json()
                self.receipt_ids.append(receipt_data.get('id'))
                
                category = receipt_data.get('category', '')
                merchant = receipt_data.get('merchant_name', '')
                amount = receipt_data.get('total_amount', '')
                status = receipt_data.get('processing_status', '')
                confidence = receipt_data.get('category_confidence', 0)
                method = receipt_data.get('categorization_method', '')
                
                success = (status == 'completed' and 
                          'walmart' in merchant.lower() if merchant else False)
                
                details = f"Category: {category}, Merchant: {merchant}, Amount: {amount}, Status: {status}, ML Confidence: {confidence}, Method: {method}"
                self.log_test("Walmart Receipt Upload & Processing", success, details)
                
                # Check if ML categorization worked for groceries
                groceries_success = ('groceries' in category.lower() and 
                                   confidence > 0.3 and method == 'advanced_ml')
                self.log_test("Walmart ML Category Prediction", groceries_success, 
                             f"Expected: Groceries, Got: {category} (confidence: {confidence})")
                
                return success
            else:
                self.log_test("Walmart Receipt Upload", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Walmart Receipt Upload", False, str(e))
            return False

    def test_upload_netflix_pdf(self):
        """Test Netflix PDF receipt upload and ML categorization"""
        print("\n🎬 TESTING NETFLIX PDF (ENTERTAINMENT CATEGORY)")
        
        try:
            test_pdf = self.create_netflix_pdf()
            
            files = {'file': ('netflix_receipt.pdf', test_pdf, 'application/pdf')}
            data = {'category': 'Auto-Detect'}
            
            response = requests.post(f"{self.api_url}/receipts/upload", 
                                   data=data, files=files, timeout=30)
            
            if response.status_code == 200:
                receipt_data = response.json()
                self.receipt_ids.append(receipt_data.get('id'))
                
                category = receipt_data.get('category', '')
                merchant = receipt_data.get('merchant_name', '')
                amount = receipt_data.get('total_amount', '')
                status = receipt_data.get('processing_status', '')
                confidence = receipt_data.get('category_confidence', 0)
                method = receipt_data.get('categorization_method', '')
                
                success = (status == 'completed' and 
                          'netflix' in merchant.lower() if merchant else False)
                
                details = f"Category: {category}, Merchant: {merchant}, Amount: {amount}, Status: {status}, ML Confidence: {confidence}, Method: {method}"
                self.log_test("Netflix PDF Upload & Processing", success, details)
                
                # Check if ML categorization worked for entertainment
                entertainment_success = ('entertainment' in category.lower() and 
                                       confidence > 0.3 and method == 'advanced_ml')
                self.log_test("Netflix ML Category Prediction", entertainment_success, 
                             f"Expected: Entertainment, Got: {category} (confidence: {confidence})")
                
                return success
            else:
                self.log_test("Netflix PDF Upload", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Netflix PDF Upload", False, str(e))
            return False

    def test_core_api_endpoints(self):
        """Test all core API endpoints"""
        print("\n🔧 TESTING CORE API ENDPOINTS")
        
        endpoints = [
            ("GET", "", "API Root"),
            ("GET", "categories", "Get Categories"),
            ("GET", "receipts", "Get Receipts"),
            ("GET", "search/suggestions?q=test", "Search Suggestions")
        ]
        
        for method, endpoint, name in endpoints:
            try:
                url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
                response = requests.get(url, timeout=10)
                success = response.status_code == 200
                self.log_test(name, success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(name, False, str(e))

    def test_receipt_operations(self):
        """Test receipt CRUD operations"""
        print("\n📄 TESTING RECEIPT OPERATIONS")
        
        if not self.receipt_ids:
            self.log_test("Receipt Operations", False, "No receipts available for testing")
            return
        
        receipt_id = self.receipt_ids[0]
        
        # Test get receipt by ID
        try:
            response = requests.get(f"{self.api_url}/receipts/{receipt_id}", timeout=10)
            success = response.status_code == 200
            self.log_test("Get Receipt by ID", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Receipt by ID", False, str(e))
        
        # Test get original file
        try:
            response = requests.get(f"{self.api_url}/receipts/{receipt_id}/file", timeout=10)
            success = response.status_code == 200
            self.log_test("Get Original Receipt File", success, 
                         f"Status: {response.status_code}, Size: {len(response.content)} bytes")
        except Exception as e:
            self.log_test("Get Original Receipt File", False, str(e))
        
        # Test update category
        try:
            response = requests.put(f"{self.api_url}/receipts/{receipt_id}/category", 
                                  json={"category": "Travel"}, timeout=10)
            success = response.status_code == 200
            self.log_test("Update Receipt Category", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Update Receipt Category", False, str(e))

    def test_export_functionality(self):
        """Test CSV export functionality"""
        print("\n📊 TESTING EXPORT FUNCTIONALITY")
        
        try:
            response = requests.post(f"{self.api_url}/receipts/export/csv", 
                                   json={}, timeout=15)
            success = response.status_code == 200
            
            if success:
                csv_content = response.content.decode('utf-8')
                lines = csv_content.split('\n')
                has_summary = 'EXPENSE SUMMARY BY CATEGORY' in csv_content
                has_details = 'DETAILED TRANSACTIONS' in csv_content
                
                details = f"Lines: {len(lines)}, Has Summary: {has_summary}, Has Details: {has_details}"
                self.log_test("CSV Export", success, details)
            else:
                self.log_test("CSV Export", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("CSV Export", False, str(e))

    def test_enhanced_amount_detection(self):
        """Test enhanced amount detection patterns"""
        print("\n💰 TESTING ENHANCED AMOUNT DETECTION")
        
        # Test various amount formats
        amount_tests = [
            ("TOTAL: $15.92", "$15.92"),
            ("AMOUNT DUE $9.72", "$9.72"),
            ("BALANCE: $49.14", "$49.14")
        ]
        
        for i, (text_pattern, expected_amount) in enumerate(amount_tests):
            try:
                # Create simple test image with amount pattern
                test_content = f"TEST RECEIPT\nDate: 12/15/2024\n{text_pattern}"
                test_image = io.BytesIO(test_content.encode())
                
                files = {'file': (f'amount_test_{i}.txt', test_image, 'text/plain')}
                data = {'category': 'Auto-Detect'}
                
                response = requests.post(f"{self.api_url}/receipts/upload", 
                                       data=data, files=files, timeout=20)
                
                if response.status_code == 200:
                    receipt_data = response.json()
                    detected_amount = receipt_data.get('total_amount', '')
                    
                    # Check if amount was detected correctly
                    amount_match = expected_amount.replace('$', '').replace('.', '') in detected_amount.replace('$', '').replace('.', '')
                    
                    self.log_test(f"Amount Detection - {text_pattern}", amount_match, 
                                 f"Expected: {expected_amount}, Got: {detected_amount}")
                else:
                    self.log_test(f"Amount Detection - {text_pattern}", False, 
                                 f"Upload failed: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Amount Detection - {text_pattern}", False, str(e))

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 LUMINA FINAL COMPREHENSIVE TEST")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Test ML System
        self.test_ml_endpoints()
        
        # Test Core API
        self.test_core_api_endpoints()
        
        # Test Upload System with ML Categorization
        self.test_upload_starbucks_receipt()
        self.test_upload_walmart_receipt()
        self.test_upload_netflix_pdf()
        
        # Test Receipt Operations
        self.test_receipt_operations()
        
        # Test Export
        self.test_export_functionality()
        
        # Test Enhanced OCR
        self.test_enhanced_amount_detection()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("🎯 FINAL COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! System is production-ready")
        elif success_rate >= 80:
            print("✅ GOOD! System is mostly functional with minor issues")
        elif success_rate >= 70:
            print("⚠️ ACCEPTABLE! System works but needs improvements")
        else:
            print("❌ NEEDS WORK! System has significant issues")
        
        print("=" * 60)
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = LuminaComprehensiveTest()
    tester.run_comprehensive_test()