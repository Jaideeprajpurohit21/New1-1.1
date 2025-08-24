from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
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


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Lumina - Receipt OCR API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

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

# OCR Processing with EasyOCR
class ReceiptOCRProcessor:
    def __init__(self):
        self.reader = None
        self.initialize_reader()
    
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
    
    async def process_receipt_image(self, image_path: str) -> Dict[str, Any]:
        """Process receipt image and extract structured data"""
        if not self.reader:
            return {
                'success': False,
                'error': 'OCR service not available'
            }
        
        try:
            # Run OCR processing in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self.reader.readtext, image_path)
            
            # Extract full text
            full_text = ' '.join([result[1] for result in results if result[2] > 0.3])  # Filter by confidence
            
            # Parse receipt data
            receipt_data = self.parse_receipt_text(full_text, results)
            receipt_data['raw_text'] = full_text
            receipt_data['success'] = True
            
            return receipt_data
            
        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to process receipt: {str(e)}'
            }
    
    def parse_receipt_text(self, full_text: str, ocr_results: List) -> Dict[str, Any]:
        """Parse OCR results into structured receipt data"""
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
                'confidence_score': 0.0
            }
            
            # Patterns for parsing
            date_patterns = [
                r'\d{1,2}/\d{1,2}/\d{2,4}',
                r'\d{1,2}-\d{1,2}-\d{2,4}',
                r'\d{4}-\d{1,2}-\d{1,2}'
            ]
            
            amount_pattern = r'\$?\d+\.?\d{0,2}'
            total_keywords = ['total', 'amount', 'sum', 'balance']
            
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
                'confidence_score': 0.0
            }

# Initialize OCR processor
ocr_processor = ReceiptOCRProcessor()

# Helper functions
async def save_uploaded_file(upload_file: UploadFile) -> str:
    """Save uploaded file to temporary location"""
    try:
        # Create temp directory if it doesn't exist
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(upload_file.filename).suffix.lower()
        if file_extension not in ['.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp']:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = temp_dir / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as buffer:
            content = await upload_file.read()
            await buffer.write(content)
        
        return str(file_path)
        
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
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
    return {"message": "Lumina Receipt OCR API", "version": "1.0.0", "status": "operational"}

@api_router.post("/receipts/upload", response_model=Receipt)
async def upload_receipt(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = "Uncategorized"
):
    """Upload and process a receipt"""
    file_path = None
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Save uploaded file
        file_path = await save_uploaded_file(file)
        
        # Create receipt record
        receipt_data = {
            "id": str(uuid.uuid4()),
            "filename": file.filename,
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
        ocr_result = await ocr_processor.process_receipt_image(file_path)
        
        # Update receipt with OCR results
        if ocr_result.get('success'):
            update_data = {
                "processing_status": "completed",
                "raw_text": ocr_result.get('raw_text', ''),
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
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_file, file_path)
        
        # Return updated receipt
        receipt_data.update(update_data)
        return Receipt(**receipt_data)
        
    except HTTPException:
        if file_path:
            cleanup_file(file_path)
        raise
    except Exception as e:
        if file_path:
            cleanup_file(file_path)
        logger.error(f"Error processing receipt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process receipt")

@api_router.get("/receipts", response_model=List[Receipt])
async def get_receipts(skip: int = 0, limit: int = 100):
    """Get all receipts with pagination"""
    try:
        receipts = await db.receipts.find().skip(skip).limit(limit).sort("upload_date", -1).to_list(length=None)
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
    """Delete a receipt"""
    try:
        result = await db.receipts.delete_one({"id": receipt_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Receipt not found")
        return {"message": "Receipt deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting receipt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete receipt")

@api_router.get("/receipts/export/csv")
async def export_receipts_csv():
    """Export all receipts as CSV"""
    try:
        receipts = await db.receipts.find().to_list(length=None)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Filename', 'Upload Date', 'Merchant Name', 'Receipt Date',
            'Total Amount', 'Category', 'Processing Status', 'Confidence Score', 'Items Count'
        ])
        
        # Write data
        for receipt in receipts:
            writer.writerow([
                receipt.get('id', ''),
                receipt.get('filename', ''),
                receipt.get('upload_date', ''),
                receipt.get('merchant_name', ''),
                receipt.get('receipt_date', ''),
                receipt.get('total_amount', ''),
                receipt.get('category', ''),
                receipt.get('processing_status', ''),
                receipt.get('confidence_score', 0.0),
                len(receipt.get('items', []))
            ])
        
        # Create response
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="lumina_receipts.csv"'}
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export receipts")

@api_router.get("/categories")
async def get_categories():
    """Get all unique categories"""
    try:
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        categories = await db.receipts.aggregate(pipeline).to_list(length=None)
        
        result = []
        for cat in categories:
            result.append({
                "name": cat["_id"] if cat["_id"] else "Uncategorized",
                "count": cat["count"]
            })
        
        return {"categories": result}
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")

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