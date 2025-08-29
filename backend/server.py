from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import asyncio
import aiofiles
import shutil
import tempfile
import json
import io
import csv
import re
from pdf2image import convert_from_path
import tempfile


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Lumina - Enhanced Receipt OCR API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Create uploads directory for permanent storage
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Mount static files for serving uploaded receipts
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class ReceiptItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    amount: Optional[str] = None
    confidence: Optional[float] = None
    
class Receipt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_file_path: Optional[str] = None  # New field for permanent storage
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    merchant_name: Optional[str] = None
    receipt_date: Optional[str] = None
    total_amount: Optional[str] = None
    category: str = "Uncategorized"
    items: List[ReceiptItem] = []
    raw_text: str = ""
    processing_status: str = "pending"  # pending, processing, completed, failed
    confidence_score: Optional[float] = None

class ReceiptCreate(BaseModel):
    filename: str
    category: Optional[str] = "Uncategorized"

class CategoryUpdate(BaseModel):
    category: str

class ExportFilters(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    categories: Optional[List[str]] = None

# Enhanced OCR Processing with PDF support and Auto-categorization
class ReceiptOCRProcessor:
    def __init__(self):
        self.reader = None
        self.initialize_reader()
        
        # Auto-categorization rules
        self.category_rules = {
            'Meals & Entertainment': [
                'starbucks', 'mcdonalds', 'cafe', 'restaurant', 'burger king', 
                'taco bell', 'kfc', 'pizza', 'subway', 'dunkin', 'chipotle',
                'bar', 'pub', 'grill', 'bistro', 'diner', 'food truck'
            ],
            'Groceries': [
                'walmart', 'target', 'grocery', 'supermarket', 'market', 
                'kroger', 'safeway', 'whole foods', 'trader joe', 'costco',
                'sam\'s club', 'food lion', 'publix', 'albertsons'
            ],
            'Transportation & Fuel': [
                'chevron', 'shell', 'gas station', 'exxon', 'bp', 'mobil',
                'texaco', 'arco', 'uber', 'lyft', 'taxi', 'parking',
                'metro', 'bus', 'train', 'airline', 'airport'
            ],
            'Office Supplies': [
                'office depot', 'staples', 'best buy', 'electronics',
                'computer', 'software', 'supplies', 'printer', 'paper'
            ],
            'Shopping': [
                'amazon', 'apple.com', 'ebay', 'etsy', 'shopping', 'store',
                'mall', 'outlet', 'retail', 'clothing', 'shoes', 'fashion'
            ],
            'Utilities': [
                'at&t', 'verizon', 'electric', 'utility', 'phone', 'internet',
                'cable', 'water', 'gas', 'power', 'energy', 'comcast',
                'spectrum', 't-mobile', 'sprint'
            ],
            'Healthcare': [
                'pharmacy', 'cvs', 'walgreens', 'hospital', 'clinic',
                'medical', 'doctor', 'dentist', 'health'
            ],
            'Travel': [
                'hotel', 'motel', 'airline', 'booking', 'expedia',
                'airbnb', 'rental car', 'hertz', 'enterprise', 'avis'
            ]
        }
    
    def initialize_reader(self):
        """Initialize EasyOCR reader"""
        try:
            import easyocr
            self.reader = easyocr.Reader(['en'], gpu=False)  # Use CPU for better compatibility
            logger.info("EasyOCR initialized successfully")
        except ImportError:
            logger.error("EasyOCR not installed. Install with: pip install easyocr")
            self.reader = None
        except Exception as e:
            logger.error(f"Error initializing EasyOCR: {str(e)}")
            self.reader = None
    
    def auto_categorize(self, merchant_name: str, raw_text: str) -> str:
        """Automatically categorize receipt based on merchant name and text"""
        if not merchant_name and not raw_text:
            return "Uncategorized"
        
        # Combine merchant name and raw text for analysis
        analysis_text = f"{merchant_name or ''} {raw_text or ''}".lower()
        
        # Check each category's keywords
        for category, keywords in self.category_rules.items():
            for keyword in keywords:
                if keyword in analysis_text:
                    logger.info(f"Auto-categorized as '{category}' based on keyword '{keyword}'")
                    return category
        
        return "Uncategorized"
    
    async def convert_pdf_to_images(self, pdf_path: str) -> List[str]:
        """Convert PDF pages to images for OCR processing"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            image_paths = []
            
            for i, image in enumerate(images):
                # Save each page as a temporary image
                temp_image_path = f"{pdf_path}_page_{i}.png"
                image.save(temp_image_path, 'PNG')
                image_paths.append(temp_image_path)
            
            return image_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            return []
    
    async def process_receipt_file(self, file_path: str, is_pdf: bool = False) -> Dict[str, Any]:
        """Process receipt file (image or PDF) and extract structured data"""
        if not self.reader:
            return {
                'success': False,
                'error': 'OCR service not available'
            }
        
        try:
            image_paths = []
            
            if is_pdf:
                # Convert PDF to images first
                image_paths = await self.convert_pdf_to_images(file_path)
                if not image_paths:
                    return {
                        'success': False,
                        'error': 'Failed to convert PDF to images'
                    }
            else:
                image_paths = [file_path]
            
            # Process all images (or single image)
            all_results = []
            combined_text = ""
            
            for image_path in image_paths:
                # Run OCR processing in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(None, self.reader.readtext, image_path)
                all_results.extend(results)
                
                # Clean up temporary PDF conversion files
                if is_pdf and image_path != file_path:
                    try:
                        os.remove(image_path)
                    except:
                        pass
            
            # Extract full text
            full_text = ' '.join([result[1] for result in all_results if result[2] > 0.3])  # Filter by confidence
            
            # Parse receipt data
            receipt_data = self.parse_receipt_text(full_text, all_results)
            receipt_data['raw_text'] = full_text
            receipt_data['success'] = True
            
            # Auto-categorize based on extracted data
            auto_category = self.auto_categorize(
                receipt_data.get('merchant_name', ''),
                full_text
            )
            receipt_data['suggested_category'] = auto_category
            
            return receipt_data
            
        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to process receipt: {str(e)}'
            }
    
    def parse_receipt_text(self, full_text: str, ocr_results: List) -> Dict[str, Any]:
        """Parse OCR results into structured receipt data with enhanced search text"""
        try:
            # Sort results by vertical position for better parsing
            sorted_results = sorted(ocr_results, key=lambda x: x[0][0][1])  # Sort by top-left y coordinate
            
            lines = []
            for result in sorted_results:
                bbox, text, confidence = result
                if confidence > 0.3:  # Filter low confidence results
                    lines.append({
                        'text': text.strip(),
                        'confidence': confidence,
                        'y_position': bbox[0][1]
                    })
            
            # Initialize parsed data
            parsed_data = {
                'merchant_name': None,
                'receipt_date': None,
                'total_amount': None,
                'items': [],
                'confidence_score': 0.0,
                'searchable_text': full_text  # Add for enhanced search
            }
            
            # Enhanced patterns for parsing
            date_patterns = [
                r'\d{1,2}/\d{1,2}/\d{2,4}',
                r'\d{1,2}-\d{1,2}-\d{2,4}',
                r'\d{4}-\d{1,2}-\d{1,2}',
                r'\d{1,2}\.\d{1,2}\.\d{2,4}'
            ]
            
            amount_pattern = r'\$?\d+\.?\d{0,2}'
            total_keywords = ['total', 'amount', 'sum', 'balance', 'due']
            
            confidences = []
            
            for i, line in enumerate(lines):
                text = line['text'].lower()
                confidence = line['confidence']
                confidences.append(confidence)
                
                # Try to identify merchant (usually first substantial line without numbers)
                if not parsed_data['merchant_name'] and len(line['text']) > 3:
                    if not re.search(r'\d', text) and not any(keyword in text for keyword in total_keywords):
                        parsed_data['merchant_name'] = line['text'].strip()
                
                # Look for dates
                if not parsed_data['receipt_date']:
                    for date_pattern in date_patterns:
                        date_match = re.search(date_pattern, text)
                        if date_match:
                            parsed_data['receipt_date'] = date_match.group()
                            break
                
                # Look for total amount
                if not parsed_data['total_amount']:
                    if any(keyword in text for keyword in total_keywords):
                        amount_match = re.search(amount_pattern, line['text'])
                        if amount_match:
                            parsed_data['total_amount'] = amount_match.group()
                
                # Look for line items (text with amounts, excluding totals)
                amount_match = re.search(amount_pattern, line['text'])
                if amount_match and not any(keyword in text for keyword in ['total', 'subtotal', 'tax', 'change']):
                    item_text = line['text'].replace(amount_match.group(), '').strip()
                    if item_text and len(item_text) > 2:
                        parsed_data['items'].append({
                            'description': item_text,
                            'amount': amount_match.group(),
                            'confidence': confidence
                        })
            
            # Calculate average confidence
            if confidences:
                parsed_data['confidence_score'] = sum(confidences) / len(confidences)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing receipt text: {str(e)}")
            return {
                'merchant_name': None,
                'receipt_date': None,
                'total_amount': None,
                'items': [],
                'confidence_score': 0.0,
                'searchable_text': full_text
            }

# Initialize OCR processor
ocr_processor = ReceiptOCRProcessor()

# Helper functions
async def save_uploaded_file_permanently(upload_file: UploadFile, receipt_id: str) -> str:
    """Save uploaded file to permanent storage directory"""
    try:
        # Generate unique filename with original extension
        file_extension = Path(upload_file.filename).suffix.lower()
        if file_extension not in ['.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp']:
            raise HTTPException(status_code=400, detail="Unsupported file format. Supports JPG, PNG, PDF, TIFF, and BMP files.")
        
        # Create filename: receiptID_originalname.ext
        safe_filename = f"{receipt_id}_{upload_file.filename}"
        file_path = UPLOADS_DIR / safe_filename
        
        # Save file permanently
        async with aiofiles.open(file_path, 'wb') as buffer:
            content = await upload_file.read()
            await buffer.write(content)
        
        return str(file_path)
        
    except Exception as e:
        logger.error(f"Error saving file permanently: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

def cleanup_file(file_path: str):
    """Clean up temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")

def prepare_for_mongo(data: dict) -> dict:
    """Prepare data for MongoDB storage"""
    if isinstance(data.get('upload_date'), datetime):
        data['upload_date'] = data['upload_date'].isoformat()
    return data

def parse_from_mongo(item: dict) -> dict:
    """Parse data from MongoDB"""
    if isinstance(item.get('upload_date'), str):
        try:
            item['upload_date'] = datetime.fromisoformat(item['upload_date'])
        except:
            item['upload_date'] = datetime.now(timezone.utc)
    return item

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Lumina Enhanced Receipt OCR API", "version": "2.0.0", "status": "operational"}

@api_router.post("/receipts/upload", response_model=Receipt)
async def upload_receipt(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = "Auto-Detect"
):
    """Upload and process a receipt (supports images and PDFs)"""
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = Path(file.filename).suffix.lower()
        is_pdf = file_extension == '.pdf'
        
        # Generate receipt ID
        receipt_id = str(uuid.uuid4())
        
        # Save file permanently
        permanent_file_path = await save_uploaded_file_permanently(file, receipt_id)
        
        # Create receipt record with permanent file path
        receipt_data = {
            "id": receipt_id,
            "filename": file.filename,
            "original_file_path": permanent_file_path,
            "upload_date": datetime.now(timezone.utc),
            "category": category,
            "processing_status": "processing",
            "raw_text": "",
            "merchant_name": None,
            "receipt_date": None,
            "total_amount": None,
            "items": [],
            "confidence_score": 0.0
        }
        
        # Insert initial record
        receipt_dict = prepare_for_mongo(receipt_data.copy())
        await db.receipts.insert_one(receipt_dict)
        
        # Process OCR
        ocr_result = await ocr_processor.process_receipt_file(permanent_file_path, is_pdf)
        
        # Update receipt with OCR results
        if ocr_result.get('success'):
            # Use auto-categorization if category is "Auto-Detect"
            final_category = category
            if category == "Auto-Detect":
                final_category = ocr_result.get('suggested_category', 'Uncategorized')
            
            update_data = {
                "processing_status": "completed",
                "category": final_category,
                "raw_text": ocr_result.get('raw_text', ''),
                "searchable_text": ocr_result.get('searchable_text', ''),
                "merchant_name": ocr_result.get('merchant_name'),
                "receipt_date": ocr_result.get('receipt_date'),
                "total_amount": ocr_result.get('total_amount'),
                "confidence_score": ocr_result.get('confidence_score', 0.0),
                "items": [
                    {
                        "id": str(uuid.uuid4()),
                        "description": item.get('description', ''),
                        "amount": item.get('amount'),
                        "confidence": item.get('confidence', 0.0)
                    }
                    for item in ocr_result.get('items', [])
                ]
            }
        else:
            update_data = {
                "processing_status": "failed",
                "raw_text": f"Error: {ocr_result.get('error', 'Unknown error')}"
            }
        
        # Update in database
        await db.receipts.update_one(
            {"id": receipt_data["id"]},
            {"$set": update_data}
        )
        
        # Return updated receipt
        receipt_data.update(update_data)
        return Receipt(**receipt_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process receipt")

@api_router.get("/receipts", response_model=List[Receipt])
async def get_receipts(
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search through all receipt text"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get all receipts with optional search and filtering"""
    try:
        # Build MongoDB query
        query = {}
        
        # Add search filter
        if search:
            query["$or"] = [
                {"merchant_name": {"$regex": search, "$options": "i"}},
                {"filename": {"$regex": search, "$options": "i"}},
                {"raw_text": {"$regex": search, "$options": "i"}},
                {"searchable_text": {"$regex": search, "$options": "i"}},
                {"items.description": {"$regex": search, "$options": "i"}}
            ]
        
        # Add category filter
        if category and category != "All":
            query["category"] = category
        
        receipts = await db.receipts.find(query).skip(skip).limit(limit).sort("upload_date", -1).to_list(length=None)
        return [Receipt(**parse_from_mongo(receipt)) for receipt in receipts]
    except Exception as e:
        logger.error(f"Error retrieving receipts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve receipts")

@api_router.get("/receipts/{receipt_id}", response_model=Receipt)
async def get_receipt(receipt_id: str):
    """Get a specific receipt by ID"""
    try:
        receipt = await db.receipts.find_one({"id": receipt_id})
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        return Receipt(**parse_from_mongo(receipt))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving receipt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve receipt")

@api_router.get("/receipts/{receipt_id}/file")
async def get_receipt_file(receipt_id: str):
    """Get the original uploaded receipt file"""
    try:
        receipt = await db.receipts.find_one({"id": receipt_id})
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        file_path = receipt.get('original_file_path')
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Original file not found")
        
        # Return the file for viewing
        return FileResponse(
            file_path,
            filename=receipt.get('filename', 'receipt'),
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving receipt file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve receipt file")

@api_router.put("/receipts/{receipt_id}/category")
async def update_receipt_category(receipt_id: str, category_update: CategoryUpdate):
    """Update receipt category"""
    try:
        result = await db.receipts.update_one(
            {"id": receipt_id},
            {"$set": {"category": category_update.category}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        return {"message": "Category updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating category: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update category")

@api_router.delete("/receipts/{receipt_id}")
async def delete_receipt(receipt_id: str):
    """Delete a receipt and its associated file"""
    try:
        # Get receipt to find file path
        receipt = await db.receipts.find_one({"id": receipt_id})
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Delete from database
        result = await db.receipts.delete_one({"id": receipt_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Delete associated file
        file_path = receipt.get('original_file_path')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not delete file {file_path}: {str(e)}")
        
        return {"message": "Receipt deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting receipt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete receipt")

@api_router.post("/receipts/export/csv")
async def export_receipts_csv(filters: ExportFilters = None):
    """Export receipts as CSV with filtering options and tax summary"""
    try:
        # Build query based on filters
        query = {}
        
        if filters:
            if filters.start_date or filters.end_date:
                date_query = {}
                if filters.start_date:
                    date_query["$gte"] = filters.start_date
                if filters.end_date:
                    date_query["$lte"] = filters.end_date
                query["upload_date"] = date_query
            
            if filters.categories:
                query["category"] = {"$in": filters.categories}
        
        receipts = await db.receipts.find(query).sort("upload_date", -1).to_list(length=None)
        
        # Create CSV in memory with enhanced tax-ready format
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write summary header
        writer.writerow(['Lumina Receipt Export - Tax Summary'])
        writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
        if filters and (filters.start_date or filters.end_date):
            writer.writerow(['Date Range:', f"{filters.start_date or 'All'} to {filters.end_date or 'All'}"])
        
        writer.writerow([])  # Empty row
        
        # Calculate category totals
        category_totals = {}
        grand_total = 0.0
        
        for receipt in receipts:
            category = receipt.get('category', 'Uncategorized')
            amount_str = receipt.get('total_amount', '0')
            try:
                amount = float(re.sub(r'[^\d.]', '', amount_str)) if amount_str else 0.0
            except:
                amount = 0.0
            
            category_totals[category] = category_totals.get(category, 0.0) + amount
            grand_total += amount
        
        # Write category summary
        writer.writerow(['EXPENSE SUMMARY BY CATEGORY'])
        writer.writerow(['Category', 'Total Amount', 'Count'])
        for category, total in sorted(category_totals.items()):
            count = len([r for r in receipts if r.get('category') == category])
            writer.writerow([category, f'${total:.2f}', count])
        
        writer.writerow(['GRAND TOTAL', f'${grand_total:.2f}', len(receipts)])
        writer.writerow([])  # Empty row
        
        # Write detailed transaction header
        writer.writerow(['DETAILED TRANSACTIONS'])
        writer.writerow([
            'Date', 'Merchant', 'Category', 'Amount', 'Receipt File', 
            'Confidence Score', 'Items Count', 'Processing Status'
        ])
        
        # Write transaction data
        for receipt in receipts:
            writer.writerow([
                receipt.get('receipt_date', receipt.get('upload_date', '')),
                receipt.get('merchant_name', ''),
                receipt.get('category', ''),
                receipt.get('total_amount', ''),
                receipt.get('filename', ''),
                f"{receipt.get('confidence_score', 0.0):.2f}",
                len(receipt.get('items', [])),
                receipt.get('processing_status', '')
            ])
        
        # Create response
        output.seek(0)
        
        # Generate filename with date range
        date_suffix = ""
        if filters and (filters.start_date or filters.end_date):
            date_suffix = f"_{filters.start_date or 'start'}_to_{filters.end_date or 'end'}"
        
        filename = f"lumina_receipts_tax_export{date_suffix}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export receipts")

@api_router.get("/categories")
async def get_categories():
    """Get all unique categories with counts"""
    try:
        pipeline = [
            {
                "$addFields": {
                    "amount_numeric": {
                        "$cond": {
                            "if": {"$and": [{"$ne": ["$total_amount", None]}, {"$ne": ["$total_amount", ""]}]},
                            "then": {
                                "$toDouble": {
                                    "$replaceAll": {
                                        "input": "$total_amount",
                                        "find": "$",
                                        "replacement": ""
                                    }
                                }
                            },
                            "else": 0
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$category", 
                    "count": {"$sum": 1}, 
                    "total_amount": {"$sum": "$amount_numeric"}
                }
            },
            {"$sort": {"count": -1}}
        ]
        categories = await db.receipts.aggregate(pipeline).to_list(length=None)
        
        result = []
        for cat in categories:
            result.append({
                "name": cat["_id"] if cat["_id"] else "Uncategorized",
                "count": cat["count"],
                "total_amount": cat.get("total_amount", 0.0)
            })
        
        return {"categories": result}
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")

@api_router.get("/search/suggestions")
async def get_search_suggestions(q: str = Query(..., min_length=2)):
    """Get search suggestions based on merchant names and receipt text"""
    try:
        # Search for matching merchants and common terms
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"merchant_name": {"$regex": q, "$options": "i"}},
                        {"searchable_text": {"$regex": q, "$options": "i"}}
                    ]
                }
            },
            {
                "$group": {
                    "_id": "$merchant_name",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        results = await db.receipts.aggregate(pipeline).to_list(length=None)
        suggestions = [{"text": result["_id"], "count": result["count"]} for result in results if result["_id"]]
        
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        return {"suggestions": []}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)