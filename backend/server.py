#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Backend Server Module

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.

PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
This software contains confidential and proprietary information of Jaideep Singh Rajpurohit.
Any reproduction, distribution, or transmission of this software, in whole or in part,
without the prior written consent of Jaideep Singh Rajpurohit is strictly prohibited.

Trade secrets contained herein are protected under applicable laws.
Unauthorized disclosure may result in civil and criminal prosecution.

For licensing information, contact: legal@luminatech.com
"""

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query, Depends
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

# Import the transaction processor
import sys
sys.path.append('..')
from transaction_processor import TransactionProcessor

# Import ML API router
try:
    sys.path.append('..')
    from ml_trainer_api import ml_router
    ML_API_AVAILABLE = True
except ImportError:
    ML_API_AVAILABLE = False
    logging.warning("ML API not available")

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
    category_confidence: Optional[float] = None  # ML category prediction confidence
    categorization_method: Optional[str] = None  # Method used for categorization

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
        
        # Initialize the advanced transaction processor
        self.transaction_processor = TransactionProcessor()
        logger.info("Initialized advanced transaction processor with ML-powered category prediction")
        
        # Legacy category rules (keeping as fallback)
        self.legacy_category_rules = {
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
        """Initialize EasyOCR reader with GPU acceleration"""
        try:
            import easyocr
            # Try GPU first, fallback to CPU if GPU not available
            try:
                self.reader = easyocr.Reader(['en'], gpu=True)
                logger.info("EasyOCR initialized successfully with GPU acceleration")
            except Exception as gpu_error:
                logger.warning(f"GPU initialization failed ({gpu_error}), falling back to CPU")
                self.reader = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR initialized successfully with CPU")
        except ImportError:
            logger.error("EasyOCR not installed. Install with: pip install easyocr")
            self.reader = None
        except Exception as e:
            logger.error(f"Error initializing EasyOCR: {str(e)}")
            self.reader = None
    
    def auto_categorize(self, merchant_name: str, raw_text: str) -> Dict[str, Any]:
        """Advanced categorization using transaction processor with confidence scoring"""
        try:
            # Use transaction processor for advanced category prediction
            full_text = f"{merchant_name or ''} {raw_text or ''}".strip()
            if not full_text:
                return {
                    'category': 'Uncategorized',
                    'confidence': 0.0,
                    'method': 'default'
                }
            
            # Get prediction from transaction processor
            result = self.transaction_processor.process_transaction(full_text)
            
            category = result.get('category', 'Uncategorized')
            confidence = result.get('confidence', 0.0)
            
            logger.info(f"Advanced auto-categorization: '{category}' (confidence: {confidence:.3f}) "
                       f"for merchant: {merchant_name}, text: {raw_text[:50]}...")
            
            return {
                'category': category,
                'confidence': confidence,
                'method': 'advanced_ml',
                'merchant': result.get('merchant'),
                'processing_status': result.get('processing_status', 'completed')
            }
            
        except Exception as e:
            logger.error(f"Error in advanced categorization: {str(e)}")
            # Fallback to legacy categorization
            return self._legacy_auto_categorize(merchant_name, raw_text)
    
    def _legacy_auto_categorize(self, merchant_name: str, raw_text: str) -> Dict[str, Any]:
        """Legacy categorization method as fallback"""
        if not merchant_name and not raw_text:
            return {
                'category': 'Uncategorized',
                'confidence': 0.0,
                'method': 'legacy_fallback'
            }
        
        # Combine merchant name and raw text for analysis
        analysis_text = f"{merchant_name or ''} {raw_text or ''}".lower()
        
        # Check each category's keywords
        for category, keywords in self.legacy_category_rules.items():
            for keyword in keywords:
                if keyword in analysis_text:
                    logger.info(f"Legacy auto-categorized as '{category}' based on keyword '{keyword}'")
                    return {
                        'category': category,
                        'confidence': 0.8,  # High confidence for direct keyword matches
                        'method': 'legacy_keywords'
                    }
        
        return {
            'category': 'Uncategorized',
            'confidence': 0.0,
            'method': 'legacy_fallback'
        }
    
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
        """Process receipt file (image or PDF) and extract structured data with optimized performance"""
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
                try:
                    # Validate image file before processing
                    import cv2
                    import numpy as np
                    
                    # Read image to check if it's valid
                    test_image = cv2.imread(image_path)
                    if test_image is None:
                        logger.error(f"Failed to read image file: {image_path}")
                        continue
                    
                    # Check image dimensions
                    height, width = test_image.shape[:2]
                    if height < 10 or width < 10:
                        logger.error(f"Image too small: {width}x{height}")
                        continue
                    
                    logger.info(f"Processing image: {image_path} ({width}x{height})")
                    
                    # Run OCR processing in thread pool to avoid blocking
                    # Optimize OCR with better parameters for speed and accuracy
                    loop = asyncio.get_event_loop()
                    
                    # Enhanced OCR processing with optimized parameters
                    results = await loop.run_in_executor(
                        None, 
                        lambda: self.reader.readtext(
                            image_path,
                            detail=1,                    # Return bounding box details
                            paragraph=False,             # Don't group into paragraphs for better line detection
                            width_ths=0.7,              # Adjusted for better text line detection
                            height_ths=0.7,             # Adjusted for better text line detection
                            mag_ratio=1.5,              # Increase magnification for better accuracy
                            slope_ths=0.1,              # Better slope detection for rotated text
                            ycenter_ths=0.5,            # Better vertical center detection
                            add_margin=0.1              # Add margin for better text capture
                        )
                    )
                    
                    all_results.extend(results)
                    logger.info(f"Successfully processed image {image_path}: found {len(results)} text elements")
                    
                except Exception as image_error:
                    logger.error(f"Error processing image {image_path}: {str(image_error)}")
                    # Continue processing other images if this one fails
                    continue
                finally:
                    # Clean up temporary PDF conversion files
                    if is_pdf and image_path != file_path:
                        try:
                            os.remove(image_path)
                        except:
                            pass
            
            # Extract full text with improved confidence filtering
            # Use lower confidence threshold for better text capture, but validate in parsing
            full_text = ' '.join([result[1] for result in all_results if result[2] > 0.2])
            
            # Parse receipt data with enhanced amount detection
            receipt_data = self.parse_receipt_text(full_text, all_results)
            receipt_data['raw_text'] = full_text
            receipt_data['success'] = True
            
            # Log processing results for debugging
            logger.info(f"OCR processed successfully. Found {len(all_results)} text elements, "
                       f"merchant: {receipt_data.get('merchant_name', 'N/A')}, "
                       f"total: {receipt_data.get('total_amount', 'N/A')}, "
                       f"category: {receipt_data.get('suggested_category', 'N/A')}, "
                       f"confidence: {receipt_data.get('confidence_score', 0):.2f}")
            
            return receipt_data
            
        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to process receipt: {str(e)}'
            }
    
    def parse_receipt_text(self, full_text: str, ocr_results: List) -> Dict[str, Any]:
        """Parse OCR results into structured receipt data using advanced transaction processor"""
        try:
            logger.info(f"Processing receipt text with advanced transaction processor: {full_text[:100]}...")
            
            # Use the advanced transaction processor to extract all information
            processed_transaction = self.transaction_processor.process_transaction(full_text)
            
            # Sort OCR results by vertical position for line items extraction
            sorted_results = sorted(ocr_results, key=lambda x: x[0][0][1])  
            
            lines = []
            confidences = []
            for result in sorted_results:
                bbox, text, confidence = result
                if confidence > 0.3:  # Filter low confidence results
                    lines.append({
                        'text': text.strip(),
                        'confidence': confidence,
                        'y_position': bbox[0][1]
                    })
                    confidences.append(confidence)
            
            # Extract line items (preserve existing logic for detailed receipt parsing)
            items = self._extract_line_items(lines)
            
            # Build parsed data using transaction processor results
            # Convert amount to string format for Pydantic validation
            amount = processed_transaction.get('amount')
            formatted_amount = None
            if amount is not None:
                if isinstance(amount, (int, float)):
                    formatted_amount = f"${amount:.2f}"
                else:
                    formatted_amount = str(amount)
            
            parsed_data = {
                'merchant_name': processed_transaction.get('merchant'),
                'receipt_date': processed_transaction.get('date'),
                'total_amount': formatted_amount,
                'items': items,
                'confidence_score': sum(confidences) / len(confidences) if confidences else 0.0,
                'searchable_text': full_text,
                'suggested_category': processed_transaction.get('category', 'Uncategorized'),
                'category_confidence': processed_transaction.get('confidence', 0.0),
                'categorization_method': 'advanced_ml' if processed_transaction.get('confidence', 0) > 0.3 else 'rule_based'
            }
            
            logger.info(f"Advanced processing completed - Merchant: {parsed_data['merchant_name']}, "
                       f"Amount: {parsed_data['total_amount']}, Date: {parsed_data['receipt_date']}, "
                       f"Category: {processed_transaction.get('category')} "
                       f"(confidence: {processed_transaction.get('confidence', 0):.3f})")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error in advanced receipt parsing: {str(e)}")
            # Fallback to basic extraction
            return self._fallback_parse_receipt_text(full_text, ocr_results)
    
    def _extract_line_items(self, lines: List[Dict]) -> List[Dict]:
        """Extract line items from OCR results"""
        items = []
        
        # Basic amount patterns for line items
        amount_patterns = [
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',                            # $12.34
            r'(?:₹|€|£|¥)\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',                   # ₹12.34
            r'\b(?:INR|USD|EUR|GBP)\s+\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b',       # INR 12.34
        ]
        
        exclude_keywords = ['total', 'subtotal', 'tax', 'change', 'balance', 'due', 'cash', 'tip']
        
        for line in lines:
            text_lower = line['text'].lower()
            original_text = line['text']
            confidence = line['confidence']
            
            # Skip lines with total/summary keywords
            if any(keyword in text_lower for keyword in exclude_keywords):
                continue
                
            # Look for amounts in this line
            for pattern in amount_patterns:
                amount_match = re.search(pattern, original_text, re.IGNORECASE)
                if amount_match:
                    # Extract numeric amount using transaction processor's robust extraction
                    from robust_amount_extractor import extract_amount
                    amount_value = extract_amount(amount_match.group())
                    
                    # Clean up item description
                    item_text = original_text.replace(amount_match.group(), '').strip()
                    item_text = re.sub(r'\s+', ' ', item_text)  # Normalize whitespace
                    
                    if amount_value and item_text and len(item_text) > 2:
                        items.append({
                            'description': item_text,
                            'amount': str(amount_value),
                            'confidence': confidence
                        })
                    break
        
        return items
    
    def _fallback_parse_receipt_text(self, full_text: str, ocr_results: List) -> Dict[str, Any]:
        """Fallback parsing method when advanced processor fails"""
        logger.warning("Using fallback receipt parsing method")
        
        # Basic fallback implementation
        parsed_data = {
            'merchant_name': None,
            'receipt_date': None,
            'total_amount': None,
            'items': [],
            'confidence_score': 0.0,
            'searchable_text': full_text,
            'category_prediction': {
                'category': 'Uncategorized',
                'confidence': 0.0,
                'processing_status': 'fallback'
            }
        }
        
        # Try to extract basic info using robust extractors
        try:
            from robust_amount_extractor import extract_amount
            from robust_date_extractor import extract_date
            
            amount = extract_amount(full_text)
            formatted_amount = None
            if amount is not None:
                if isinstance(amount, (int, float)):
                    formatted_amount = f"${amount:.2f}"
                else:
                    formatted_amount = str(amount)
            
            parsed_data['total_amount'] = formatted_amount
            parsed_data['receipt_date'] = extract_date(full_text)
            
            # Simple merchant extraction (first non-numeric line)
            lines = [line.split('\t')[1] if '\t' in line else line 
                    for line in full_text.split('\n')[:5]]  # First 5 lines
            for line in lines:
                if len(line.strip()) > 3 and not re.search(r'\d', line):
                    parsed_data['merchant_name'] = line.strip()
                    break
                    
        except Exception as e:
            logger.error(f"Error in fallback parsing: {str(e)}")
        
        return parsed_data
    
    def _extract_transaction_amount_robust(self, text: str) -> Optional[str]:
        """
        Robust function to extract transaction amounts from text while ignoring 
        account balances, transaction IDs, and other irrelevant numbers.
        
        Returns the amount in standardized currency format (e.g., "$485.00", "₹1500.00")
        """
        import re
        from typing import Optional, List, Tuple
        
        if not text or not isinstance(text, str):
            return None
        
        # Currency mappings for standardization
        currency_codes = ['INR', 'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'SGD', 'JPY']
        currency_symbols = ['₹', '$', '€', '£', '¥', '¢']
        currency_map = {
            'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£', 
            'CAD': '$', 'AUD': '$', 'SGD': '$', 'JPY': '¥'
        }
        
        # Transaction keywords (ordered by priority)
        transaction_keywords = [
            'purchase', 'spent', 'charged', 'debited', 'payment of', 'payment',
            'subscription of', 'subscription', 'monthly', 'billed', 'transaction',
            'withdrew', 'withdrawal', 'transfer', 'paid', 'cost', 'amount due', 'due', 'total'
        ]
        
        # Balance keywords to avoid
        balance_keywords = [
            'avl bal', 'available balance', 'balance', 'bal', 'remaining', 
            'limit', 'credit limit', 'ending in'
        ]
        
        def extract_numeric_amount(amount_str: str) -> Optional[float]:
            """Extract numeric value from amount string"""
            try:
                cleaned = amount_str
                for symbol in currency_symbols:
                    cleaned = cleaned.replace(symbol, '')
                for code in currency_codes:
                    cleaned = re.sub(r'\b' + code + r'\b', '', cleaned, flags=re.IGNORECASE)
                
                cleaned = cleaned.strip()
                
                # Handle comma-separated numbers
                number_match = re.search(r'\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?', cleaned)
                if number_match:
                    number_str = number_match.group().replace(',', '')
                    return float(number_str)
                
                # Handle simple decimal numbers
                decimal_match = re.search(r'\d+\.\d{1,2}', cleaned)
                if decimal_match:
                    return float(decimal_match.group())
                
                # Handle whole numbers
                whole_match = re.search(r'\d+', cleaned)
                if whole_match:
                    return float(whole_match.group())
                    
            except (ValueError, AttributeError):
                pass
            
            return None
        
        def detect_currency(amount_str: str) -> str:
            """Detect currency from amount string"""
            for code, symbol in currency_map.items():
                if code in amount_str.upper():
                    return symbol
            
            for symbol in currency_symbols:
                if symbol in amount_str:
                    return symbol
            
            return '$'  # Default to USD
        
        # Find amounts near transaction keywords
        text_lower = text.lower()
        found_amounts = []
        
        for priority, keyword in enumerate(transaction_keywords):
            keyword_positions = [m.start() for m in re.finditer(re.escape(keyword), text_lower)]
            
            for pos in keyword_positions:
                # Look in window around keyword
                start_pos = max(0, pos - 50)
                end_pos = min(len(text), pos + len(keyword) + 50)
                window_text = text[start_pos:end_pos]
                
                # Currency patterns
                patterns = [
                    r'\b(?:INR|USD|EUR|GBP|CAD|AUD|SGD|JPY)\s+\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b',
                    r'[₹$€£¥¢]\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?',
                    r'(?:' + re.escape(keyword) + r')\s+(?:of\s+)?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?',
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, window_text, re.IGNORECASE)
                    for match in matches:
                        amount_val = extract_numeric_amount(match.group())
                        if amount_val and 0.01 <= amount_val <= 100000:
                            currency = detect_currency(match.group())
                            distance = abs(match.start() - (pos - start_pos))
                            score = priority * 100 + distance
                            position = start_pos + match.start()
                            found_amounts.append((amount_val, currency, score, position))
        
        # If no keyword-based amounts, look for standalone currency amounts
        if not found_amounts:
            patterns = [
                r'\b(?:INR|USD|EUR|GBP|CAD|AUD|SGD|JPY)\s+\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b',
                r'[₹$€£¥¢]\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?(?!\d)',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Skip if near balance keywords
                    context_start = max(0, match.start() - 30)
                    context_end = min(len(text), match.end() + 30)
                    context = text[context_start:context_end].lower()
                    
                    if any(bal_keyword in context for bal_keyword in balance_keywords):
                        continue
                    
                    amount_val = extract_numeric_amount(match.group())
                    if amount_val and 0.01 <= amount_val <= 100000:
                        currency = detect_currency(match.group())
                        found_amounts.append((amount_val, currency, 1000, match.start()))
        
        # Return the best amount
        if found_amounts:
            found_amounts.sort(key=lambda x: (x[2], x[3]))  # Sort by score, then position
            amount, currency, _, _ = found_amounts[0]
            
            # Format with proper decimal places
            if amount == int(amount):
                return f"{currency}{int(amount)}.00"
            else:
                return f"{currency}{amount:.2f}"
        
        return None
    
    def _extract_transaction_date_robust(self, text: str) -> Optional[str]:
        """
        Robust function to extract transaction dates from text while avoiding 
        false matches with amounts, IDs, and other numbers.
        
        Returns the date in YYYY-MM-DD format.
        """
        import re
        from datetime import datetime, date
        from typing import Optional, List, Tuple
        import calendar
        
        if not text or not isinstance(text, str):
            return None
        
        # Current date for validation
        today = date.today()
        current_year = today.year
        
        # Month name mappings
        month_names = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
            'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        # Date context keywords
        date_keywords = [
            'on', 'date', 'dated', 'transaction', 'charged', 'billed', 'purchased',
            'payment', 'transfer', 'withdrawal', 'deposit', 'processed', 'completed'
        ]
        
        # Keywords to avoid
        avoid_keywords = [
            'amount', 'balance', 'total', 'price', 'cost', 'fee', 'limit', 
            'account', 'card', 'number', 'id', 'phone', 'mobile', 'contact'
        ]
        
        def validate_date(year: int, month: int, day: int) -> bool:
            """Validate if the date is reasonable for a transaction"""
            try:
                test_date = date(year, month, day)
                if test_date > today:
                    return False
                if year < current_year - 7:
                    return False
                if year < 2000:
                    return False
                return True
            except ValueError:
                return False
        
        def parse_single_date(date_str: str) -> Optional[str]:
            """Parse a single date string"""
            date_str = date_str.strip()
            
            # YYYY-MM-DD or YYYY/MM/DD
            match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
            if match:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if validate_date(year, month, day):
                    return f"{year:04d}-{month:02d}-{day:02d}"
            
            # DD-MM-YYYY or DD/MM/YYYY
            match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', date_str)
            if match:
                day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if validate_date(year, month, day):
                    return f"{year:04d}-{month:02d}-{day:02d}"
            
            # MM/DD/YY or DD/MM/YY patterns
            match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{2})', date_str)
            if match:
                first, second, year_short = int(match.group(1)), int(match.group(2)), int(match.group(3))
                year = 2000 + year_short if year_short <= 30 else 1900 + year_short
                
                # Try MM/DD/YY first
                if first <= 12 and second <= 31 and validate_date(year, first, second):
                    return f"{year:04d}-{first:02d}-{second:02d}"
                # Fallback to DD/MM/YY
                elif second <= 12 and first <= 31 and validate_date(year, second, first):
                    return f"{year:04d}-{second:02d}-{first:02d}"
            
            # Textual dates
            for month_name, month_num in month_names.items():
                # "Oct 5" or "October 5" (without year)
                pattern = rf'\b{re.escape(month_name)}\s+(\d{{1,2}})\b(?!\s*,?\s*\d{{4}})'
                match = re.search(pattern, date_str, re.IGNORECASE)
                if match:
                    day = int(match.group(1))
                    year = current_year
                    test_date = date(year, month_num, day)
                    if test_date > today:
                        year = current_year - 1
                    if validate_date(year, month_num, day):
                        return f"{year:04d}-{month_num:02d}-{day:02d}"
                
                # "Oct 5, 2024" or "October 5, 2024"
                pattern = rf'\b{re.escape(month_name)}\s+(\d{{1,2}}),?\s+(\d{{4}})\b'
                match = re.search(pattern, date_str, re.IGNORECASE)
                if match:
                    day, year = int(match.group(1)), int(match.group(2))
                    if validate_date(year, month_num, day):
                        return f"{year:04d}-{month_num:02d}-{day:02d}"
                
                # "5th Oct 2024" or "12th Mar 2024"
                pattern = rf'\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{re.escape(month_name)}\s+(\d{{4}})\b'
                match = re.search(pattern, date_str, re.IGNORECASE)
                if match:
                    day, year = int(match.group(1)), int(match.group(2))
                    if validate_date(year, month_num, day):
                        return f"{year:04d}-{month_num:02d}-{day:02d}"
            
            return None
        
        # Find date candidates
        candidates = []
        text_lower = text.lower()
        
        # High priority: Dates near date keywords
        for keyword in date_keywords:
            for match in re.finditer(re.escape(keyword), text_lower):
                start_pos = max(0, match.start() - 30)
                end_pos = min(len(text), match.end() + 30)
                context_window = text[start_pos:end_pos]
                
                date_patterns = [
                    r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
                    r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
                    r'\d{1,2}[-/]\d{1,2}[-/]\d{2}',
                    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,?\s+\d{4})?\b',
                    r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b'
                ]
                
                for pattern in date_patterns:
                    for date_match in re.finditer(pattern, context_window, re.IGNORECASE):
                        date_str = date_match.group()
                        distance = abs(date_match.start() - (match.start() - start_pos))
                        candidates.append((date_str, distance, start_pos + date_match.start()))
        
        # Medium priority: ISO-like formats
        iso_patterns = [r'\b\d{4}-\d{1,2}-\d{1,2}\b', r'\b\d{4}/\d{1,2}/\d{1,2}\b']
        for pattern in iso_patterns:
            for match in re.finditer(pattern, text):
                context_start = max(0, match.start() - 20)
                context_end = min(len(text), match.end() + 20)
                context = text[context_start:context_end].lower()
                
                if not any(avoid_word in context for avoid_word in avoid_keywords):
                    candidates.append((match.group(), 1000, match.start()))
        
        # Parse candidates and return best match
        if candidates:
            candidates.sort(key=lambda x: (x[1], x[2]))  # Sort by priority, then position
            for date_str, _, _ in candidates:
                parsed_date = parse_single_date(date_str)
                if parsed_date:
                    return parsed_date
        
        return None

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
            
            # Ensure total_amount is properly formatted as string
            total_amount = ocr_result.get('total_amount')
            formatted_amount = None
            if total_amount is not None:
                if isinstance(total_amount, (int, float)):
                    formatted_amount = f"${total_amount:.2f}"
                else:
                    formatted_amount = str(total_amount)
            
            # Format item amounts as well
            formatted_items = []
            for item in ocr_result.get('items', []):
                item_amount = item.get('amount')
                formatted_item_amount = None
                if item_amount is not None:
                    if isinstance(item_amount, (int, float)):
                        formatted_item_amount = f"${item_amount:.2f}"
                    else:
                        formatted_item_amount = str(item_amount)
                
                formatted_items.append({
                    "id": str(uuid.uuid4()),
                    "description": item.get('description', ''),
                    "amount": formatted_item_amount,
                    "confidence": item.get('confidence', 0.0)
                })
            
            update_data = {
                "processing_status": "completed",
                "category": final_category,
                "raw_text": ocr_result.get('raw_text', ''),
                "searchable_text": ocr_result.get('searchable_text', ''),
                "merchant_name": ocr_result.get('merchant_name'),
                "receipt_date": ocr_result.get('receipt_date'),
                "total_amount": formatted_amount,
                "confidence_score": ocr_result.get('confidence_score', 0.0),
                "items": formatted_items,
                "category_confidence": ocr_result.get('category_confidence', 0.0),
                "categorization_method": ocr_result.get('categorization_method', 'unknown')
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
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        categories = await db.receipts.aggregate(pipeline).to_list(length=None)
        
        result = []
        for cat in categories:
            result.append({
                "name": cat["_id"] if cat["_id"] else "Uncategorized",
                "count": cat["count"],
                "total_amount": 0.0  # Simplified for now to avoid aggregation issues
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

# Include ML router if available
if ML_API_AVAILABLE:
    app.include_router(ml_router)
    logger.info("ML API endpoints enabled")
else:
    logger.warning("ML API endpoints not available")

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