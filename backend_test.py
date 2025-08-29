import requests
import sys
import json
import io
import tempfile
import os
from datetime import datetime
from pathlib import Path

class LuminaAPITester:
    def __init__(self, base_url="https://smart-receipts-11.preview.emergentagent.com"):
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

    def create_test_pdf(self):
        """Create a simple test PDF file"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            # Create a simple PDF receipt
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            
            # Add receipt content
            c.drawString(100, 750, "STARBUCKS COFFEE")
            c.drawString(100, 730, "123 Coffee Street")
            c.drawString(100, 710, "Date: 12/15/2024")
            c.drawString(100, 690, "")
            c.drawString(100, 670, "Latte Grande        $5.25")
            c.drawString(100, 650, "Croissant          $3.50")
            c.drawString(100, 630, "")
            c.drawString(100, 610, "Subtotal           $8.75")
            c.drawString(100, 590, "Tax                $0.70")
            c.drawString(100, 570, "TOTAL              $9.45")
            
            c.save()
            pdf_buffer.seek(0)
            return pdf_buffer
            
        except ImportError:
            print("   ReportLab not available, creating simple text file as PDF")
            text_content = """STARBUCKS COFFEE
123 Coffee Street
Date: 12/15/2024
Latte Grande $5.25
Croissant $3.50
TOTAL $9.45"""
            return io.BytesIO(text_content.encode())

    def test_upload_pdf_receipt(self):
        """Test uploading a PDF receipt"""
        try:
            # Create test PDF
            test_pdf = self.create_test_pdf()
            
            files = {
                'file': ('starbucks_receipt.pdf', test_pdf, 'application/pdf')
            }
            data = {
                'category': 'Auto-Detect'  # Should auto-categorize as Meals & Entertainment
            }
            
            success, response = self.run_test(
                "Upload PDF Receipt (Auto-Detect)",
                "POST",
                "receipts/upload",
                200,
                data=data,
                files=files
            )
            
            if success and response.get('id'):
                self.pdf_receipt_id = response['id']
                print(f"   PDF Receipt ID: {self.pdf_receipt_id}")
                print(f"   Processing Status: {response.get('processing_status')}")
                print(f"   Merchant: {response.get('merchant_name')}")
                print(f"   Total: {response.get('total_amount')}")
                print(f"   Auto-categorized as: {response.get('category')}")
                print(f"   Original file path: {response.get('original_file_path')}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error creating test PDF: {str(e)}")
            return False

    def test_view_original_receipt(self):
        """Test viewing original receipt file"""
        if not self.receipt_id:
            print("❌ No receipt ID available for testing")
            return False
            
        success, response = self.run_test(
            "View Original Receipt File",
            "GET",
            f"receipts/{self.receipt_id}/file",
            200,
            response_type='file'
        )
        
        if success:
            print(f"   Original file retrieved successfully")
            print(f"   File size: {len(response)} bytes")
            
        return success

    def test_search_receipts(self):
        """Test enhanced search functionality"""
        # Test search by merchant name
        success1, response1 = self.run_test(
            "Search Receipts by Merchant",
            "GET",
            "receipts?search=SUPER",
            200
        )
        
        if success1:
            print(f"   Found {len(response1)} receipts matching 'SUPER'")
        
        # Test search by amount
        success2, response2 = self.run_test(
            "Search Receipts by Amount",
            "GET",
            "receipts?search=11.60",
            200
        )
        
        if success2:
            print(f"   Found {len(response2)} receipts matching '11.60'")
        
        return success1 and success2

    def test_category_filtering(self):
        """Test category filtering"""
        success, response = self.run_test(
            "Filter Receipts by Category",
            "GET",
            "receipts?category=Meals & Entertainment",
            200
        )
        
        if success:
            print(f"   Found {len(response)} receipts in 'Meals & Entertainment' category")
            
        return success

    def test_search_suggestions(self):
        """Test search suggestions endpoint"""
        success, response = self.run_test(
            "Get Search Suggestions",
            "GET",
            "search/suggestions?q=SUP",
            200
        )
        
        if success and response.get('suggestions'):
            print(f"   Found {len(response['suggestions'])} suggestions for 'SUP'")
            for suggestion in response['suggestions'][:3]:
                print(f"     - {suggestion.get('text')} ({suggestion.get('count')} times)")
                
        return success

    def test_export_csv_basic(self):
        """Test basic CSV export functionality"""
        success, response = self.run_test(
            "Export Receipts CSV (Basic)",
            "POST",
            "receipts/export/csv",
            200,
            data={},
            response_type='csv'
        )
        
        if success:
            try:
                csv_content = response.decode('utf-8')
                lines = csv_content.split('\n')
                print(f"   CSV has {len(lines)} lines")
                print(f"   First line: {lines[0] if lines else 'No content'}")
                
                # Check for tax-ready features
                if 'EXPENSE SUMMARY BY CATEGORY' in csv_content:
                    print("   ✅ Contains category summary")
                if 'DETAILED TRANSACTIONS' in csv_content:
                    print("   ✅ Contains detailed transactions")
                if 'Confidence Score' in csv_content:
                    print("   ✅ Contains confidence scores")
                    
            except:
                print("   CSV content received but couldn't decode")
                
        return success

    def test_export_csv_filtered(self):
        """Test CSV export with filters"""
        export_filters = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "categories": ["Meals & Entertainment", "Groceries"]
        }
        
        success, response = self.run_test(
            "Export Receipts CSV (Filtered)",
            "POST",
            "receipts/export/csv",
            200,
            data=export_filters,
            response_type='csv'
        )
        
        if success:
            try:
                csv_content = response.decode('utf-8')
                lines = csv_content.split('\n')
                print(f"   Filtered CSV has {len(lines)} lines")
                
                # Check for date range in filename/content
                if '2024-01-01' in csv_content or '2024-12-31' in csv_content:
                    print("   ✅ Date range applied")
                    
            except:
                print("   Filtered CSV content received but couldn't decode")
                
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
    
    # Test sequence for enhanced Lumina v2.0.0 features
    test_sequence = [
        ("API Root", tester.test_api_root),
        ("Get Categories (Empty)", tester.test_get_categories_empty),
        ("Get Receipts (Empty)", tester.test_get_receipts_empty),
        
        # Test image upload with auto-categorization
        ("Upload Receipt (Auto-Detect)", tester.test_upload_receipt),
        
        # Test PDF support
        ("Upload PDF Receipt", tester.test_upload_pdf_receipt),
        
        # Test receipt retrieval and file viewing
        ("Get Receipt by ID", tester.test_get_receipt_by_id),
        ("View Original Receipt File", tester.test_view_original_receipt),
        
        # Test category management
        ("Update Receipt Category", tester.test_update_receipt_category),
        ("Get Categories (With Data)", tester.test_get_categories_with_data),
        
        # Test enhanced search and filtering
        ("Search Receipts", tester.test_search_receipts),
        ("Category Filtering", tester.test_category_filtering),
        ("Search Suggestions", tester.test_search_suggestions),
        ("Get Receipts (With Data)", tester.test_get_receipts_with_data),
        
        # Test enhanced CSV export
        ("Export CSV (Basic)", tester.test_export_csv_basic),
        ("Export CSV (Filtered)", tester.test_export_csv_filtered),
        
        # Cleanup tests
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