import requests
import sys
import json
import io
import tempfile
import os
from datetime import datetime
from pathlib import Path

class LuminaAPITester:
    def __init__(self, base_url="https://expenseai-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.receipt_id = None
        self.pdf_receipt_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, response_type='json'):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {}
        
        if data and not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                if response_type == 'json' and response.content:
                    try:
                        response_data = response.json()
                        print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                        return success, response_data
                    except:
                        return success, {}
                else:
                    return success, response.content
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        return success

    def test_get_categories_empty(self):
        """Test getting categories when empty"""
        success, response = self.run_test(
            "Get Categories (Empty)",
            "GET",
            "categories",
            200
        )
        return success

    def test_get_receipts_empty(self):
        """Test getting receipts when empty"""
        success, response = self.run_test(
            "Get Receipts (Empty)",
            "GET",
            "receipts",
            200
        )
        return success

    def create_test_image(self):
        """Create a simple test image file"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple receipt-like image
            img = Image.new('RGB', (400, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Add some text that looks like a receipt
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            receipt_text = [
                "SUPER MARKET",
                "123 Main Street",
                "City, State 12345",
                "",
                "Date: 12/15/2024",
                "Time: 14:30",
                "",
                "Apples         $3.99",
                "Bread          $2.50",
                "Milk           $4.25",
                "",
                "Subtotal      $10.74",
                "Tax            $0.86",
                "TOTAL         $11.60",
                "",
                "Thank you!"
            ]
            
            y_position = 50
            for line in receipt_text:
                draw.text((50, y_position), line, fill='black', font=font)
                y_position += 25
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
            
        except ImportError:
            # If PIL is not available, create a simple text file as image
            print("   PIL not available, creating simple text file")
            text_content = """SUPER MARKET
123 Main Street
Date: 12/15/2024
Apples $3.99
Bread $2.50
Milk $4.25
TOTAL $11.60"""
            return io.BytesIO(text_content.encode())

    def test_upload_receipt(self):
        """Test uploading a receipt with Auto-Detect category"""
        try:
            # Create test image
            test_image = self.create_test_image()
            
            files = {
                'file': ('test_receipt.png', test_image, 'image/png')
            }
            data = {
                'category': 'Auto-Detect'  # Test AI auto-categorization
            }
            
            success, response = self.run_test(
                "Upload Receipt (Auto-Detect)",
                "POST",
                "receipts/upload",
                200,
                data=data,
                files=files
            )
            
            if success and response.get('id'):
                self.receipt_id = response['id']
                print(f"   Receipt ID: {self.receipt_id}")
                print(f"   Processing Status: {response.get('processing_status')}")
                print(f"   Merchant: {response.get('merchant_name')}")
                print(f"   Total: {response.get('total_amount')}")
                print(f"   Auto-categorized as: {response.get('category')}")
                print(f"   Original file path: {response.get('original_file_path')}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error creating test image: {str(e)}")
            return False

    def test_get_receipt_by_id(self):
        """Test getting a specific receipt by ID"""
        if not self.receipt_id:
            print("❌ No receipt ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Receipt by ID",
            "GET",
            f"receipts/{self.receipt_id}",
            200
        )
        return success

    def test_update_receipt_category(self):
        """Test updating receipt category"""
        if not self.receipt_id:
            print("❌ No receipt ID available for testing")
            return False
            
        success, response = self.run_test(
            "Update Receipt Category",
            "PUT",
            f"receipts/{self.receipt_id}/category",
            200,
            data={"category": "Travel"}
        )
        return success

    def test_get_receipts_with_data(self):
        """Test getting receipts when data exists"""
        success, response = self.run_test(
            "Get Receipts (With Data)",
            "GET",
            "receipts",
            200
        )
        
        if success and response:
            print(f"   Found {len(response)} receipts")
            
        return success

    def test_get_categories_with_data(self):
        """Test getting categories when data exists"""
        success, response = self.run_test(
            "Get Categories (With Data)",
            "GET",
            "categories",
            200
        )
        
        if success and response.get('categories'):
            print(f"   Found {len(response['categories'])} categories")
            for cat in response['categories']:
                print(f"     - {cat.get('name')}: {cat.get('count')} receipts")
                
        return success

    def test_export_csv(self):
        """Test CSV export functionality"""
        success, response = self.run_test(
            "Export Receipts CSV",
            "GET",
            "receipts/export/csv",
            200,
            response_type='csv'
        )
        
        if success:
            try:
                csv_content = response.decode('utf-8')
                lines = csv_content.split('\n')
                print(f"   CSV has {len(lines)} lines")
                print(f"   Header: {lines[0] if lines else 'No header'}")
            except:
                print("   CSV content received but couldn't decode")
                
        return success

    def test_delete_receipt(self):
        """Test deleting a receipt"""
        if not self.receipt_id:
            print("❌ No receipt ID available for testing")
            return False
            
        success, response = self.run_test(
            "Delete Receipt",
            "DELETE",
            f"receipts/{self.receipt_id}",
            200
        )
        return success

    def test_get_nonexistent_receipt(self):
        """Test getting a non-existent receipt"""
        success, response = self.run_test(
            "Get Non-existent Receipt",
            "GET",
            "receipts/nonexistent-id",
            404
        )
        return success

def main():
    print("🚀 Starting Lumina Receipt OCR API Tests")
    print("=" * 50)
    
    tester = LuminaAPITester()
    
    # Test sequence
    test_sequence = [
        ("API Root", tester.test_api_root),
        ("Get Categories (Empty)", tester.test_get_categories_empty),
        ("Get Receipts (Empty)", tester.test_get_receipts_empty),
        ("Upload Receipt", tester.test_upload_receipt),
        ("Get Receipt by ID", tester.test_get_receipt_by_id),
        ("Update Receipt Category", tester.test_update_receipt_category),
        ("Get Receipts (With Data)", tester.test_get_receipts_with_data),
        ("Get Categories (With Data)", tester.test_get_categories_with_data),
        ("Export CSV", tester.test_export_csv),
        ("Delete Receipt", tester.test_delete_receipt),
        ("Get Non-existent Receipt", tester.test_get_nonexistent_receipt),
    ]
    
    # Run all tests
    for test_name, test_func in test_sequence:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())