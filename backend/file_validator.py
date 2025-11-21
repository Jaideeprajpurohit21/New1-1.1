#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
File Validation System

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import os
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from config import settings
from logging_config import get_logger

# Optional imports with graceful fallbacks
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("Warning: python-magic not available - using fallback file type detection")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available - image validation will be limited")

try:
    import fitz  # PyMuPDF for PDF validation
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    print("Warning: PyMuPDF not available - PDF validation will be limited")

logger = get_logger("file_validator")

class FileValidator:
    """
    Comprehensive file validation system
    """
    
    # MIME type mappings for allowed file types
    ALLOWED_MIME_TYPES = {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/tiff': ['.tiff', '.tif'],
        'image/bmp': ['.bmp'],
        'application/pdf': ['.pdf'],
    }
    
    # Magic number signatures for file type detection
    FILE_SIGNATURES = {
        b'\xFF\xD8\xFF': 'image/jpeg',  # JPEG
        b'\x89PNG\r\n\x1a\n': 'image/png',  # PNG
        b'%PDF-': 'application/pdf',  # PDF
        b'BM': 'image/bmp',  # BMP
        b'II*\x00': 'image/tiff',  # TIFF (little endian)
        b'MM\x00*': 'image/tiff',  # TIFF (big endian)
    }
    
    def __init__(self):
        self.max_size = settings.max_upload_size
        self.allowed_extensions = settings.allowed_extensions
    
    def _detect_mime_type(self, file_content: bytes) -> Optional[str]:
        """
        Detect MIME type from file content using magic numbers
        """
        if MAGIC_AVAILABLE:
            try:
                # Try python-magic first (more accurate)
                mime_type = magic.from_buffer(file_content, mime=True)
                return mime_type
            except Exception as e:
                logger.debug(f"Magic library detection failed: {e}")
        
        # Fallback to signature-based detection
        for signature, mime_type in self.FILE_SIGNATURES.items():
            if file_content.startswith(signature):
                return mime_type
        
        return None
    
    def _validate_image(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Validate image file integrity
        """
        if not PIL_AVAILABLE:
            # Basic validation without PIL
            if len(file_content) > 50 * 1024 * 1024:  # 50MB limit
                return False, "Image file too large"
            return True, "Basic image validation passed (PIL not available)"
        
        try:
            import io
            # Try to open image with PIL
            image = Image.open(io.BytesIO(file_content))
            
            # Verify image can be loaded
            image.verify()
            
            # Reopen for size check (verify() closes the image)
            image = Image.open(io.BytesIO(file_content))
            
            # Check image dimensions (reasonable limits)
            width, height = image.size
            if width > 10000 or height > 10000:
                return False, f"Image dimensions too large: {width}x{height}"
            
            if width < 10 or height < 10:
                return False, f"Image dimensions too small: {width}x{height}"
            
            logger.info(f"Image validation passed: {filename} ({width}x{height})")
            return True, "Valid image file"
            
        except Exception as e:
            logger.warning(f"Image validation failed for {filename}: {e}")
            return False, f"Invalid image file: {str(e)}"
    
    def _validate_pdf(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Validate PDF file integrity
        """
        try:
            # Try to open PDF with PyMuPDF
            pdf_doc = fitz.open(stream=file_content, filetype="pdf")
            
            # Check if PDF has pages
            page_count = pdf_doc.page_count
            if page_count == 0:
                pdf_doc.close()
                return False, "PDF file has no pages"
            
            # Reasonable page limit
            if page_count > 50:
                pdf_doc.close()
                return False, f"PDF has too many pages: {page_count} (max 50)"
            
            # Try to access first page to ensure it's readable
            first_page = pdf_doc[0]
            
            pdf_doc.close()
            
            logger.info(f"PDF validation passed: {filename} ({page_count} pages)")
            return True, f"Valid PDF file with {page_count} pages"
            
        except Exception as e:
            logger.warning(f"PDF validation failed for {filename}: {e}")
            return False, f"Invalid PDF file: {str(e)}"
    
    def validate_file(self, file: UploadFile) -> Tuple[bool, str, Optional[str]]:
        """
        Comprehensive file validation
        
        Returns:
            Tuple[bool, str, Optional[str]]: (is_valid, message, detected_mime_type)
        """
        try:
            # Read file content
            file_content = file.file.read()
            file.file.seek(0)  # Reset file pointer
            
            # 1. Check file size
            file_size = len(file_content)
            if file_size == 0:
                return False, "Empty file not allowed", None
            
            if file_size > self.max_size:
                size_mb = file_size / (1024 * 1024)
                max_mb = self.max_size / (1024 * 1024)
                return False, f"File too large: {size_mb:.2f}MB (max {max_mb:.2f}MB)", None
            
            # 2. Check file extension
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                return False, f"File type not allowed: {file_extension}. Allowed types: {', '.join(self.allowed_extensions)}", None
            
            # 3. Detect MIME type from content
            detected_mime = self._detect_mime_type(file_content)
            if not detected_mime:
                return False, "Could not detect file type", None
            
            # 4. Validate MIME type matches extension
            if detected_mime not in self.ALLOWED_MIME_TYPES:
                return False, f"File type not allowed: {detected_mime}", detected_mime
            
            allowed_extensions_for_mime = self.ALLOWED_MIME_TYPES[detected_mime]
            if file_extension not in allowed_extensions_for_mime:
                return False, f"File extension {file_extension} doesn't match content type {detected_mime}", detected_mime
            
            # 5. Content-specific validation
            if detected_mime.startswith('image/'):
                is_valid, message = self._validate_image(file_content, file.filename)
                if not is_valid:
                    return False, message, detected_mime
            
            elif detected_mime == 'application/pdf':
                is_valid, message = self._validate_pdf(file_content, file.filename)
                if not is_valid:
                    return False, message, detected_mime
            
            # 6. Security check - scan for potential threats
            if self._scan_for_threats(file_content, file.filename):
                return False, "File contains potentially malicious content", detected_mime
            
            size_mb = file_size / (1024 * 1024)
            logger.info(f"File validation passed: {file.filename} ({size_mb:.2f}MB, {detected_mime})")
            
            return True, f"File validation successful ({size_mb:.2f}MB)", detected_mime
            
        except Exception as e:
            logger.error(f"File validation error for {file.filename}: {e}", exc_info=True)
            return False, f"File validation failed: {str(e)}", None
    
    def _scan_for_threats(self, file_content: bytes, filename: str) -> bool:
        """
        Basic security scanning for common threats
        """
        try:
            # Check for common malicious patterns
            malicious_patterns = [
                b'<script',  # JavaScript in uploads
                b'javascript:',  # JavaScript URLs
                b'<?php',  # PHP code
                b'<%',  # Server-side includes
                b'\x00',  # Null bytes (can be used for bypass)
            ]
            
            content_lower = file_content.lower()
            for pattern in malicious_patterns:
                if pattern in content_lower:
                    logger.warning(f"Malicious pattern detected in {filename}: {pattern}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Threat scanning error for {filename}: {e}")
            # Err on the side of caution
            return True

# Global file validator instance
file_validator = FileValidator()

def validate_upload_file(file: UploadFile):
    """
    Dependency function for file validation
    """
    is_valid, message, mime_type = file_validator.validate_file(file)
    
    if not is_valid:
        logger.warning(f"File validation failed: {file.filename} - {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid file",
                "message": message,
                "filename": file.filename,
                "allowed_types": list(settings.allowed_extensions),
                "max_size_mb": settings.max_upload_size / (1024 * 1024)
            }
        )
    
    # Add validation info to file object for later use
    file.validated_mime_type = mime_type
    file.validation_message = message
    
    return file

# Import required modules that might not be available
try:
    import io
except ImportError:
    logger.warning("io module not available")

try:
    import fitz
except ImportError:
    logger.warning("PyMuPDF not available - PDF validation will be limited")
    
    def _validate_pdf_fallback(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """Fallback PDF validation without PyMuPDF"""
        if not file_content.startswith(b'%PDF-'):
            return False, "Invalid PDF signature"
        
        # Basic checks
        if len(file_content) > 50 * 1024 * 1024:  # 50MB limit for PDFs
            return False, "PDF file too large"
        
        return True, "Basic PDF validation passed"
    
    FileValidator._validate_pdf = _validate_pdf_fallback