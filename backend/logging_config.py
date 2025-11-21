#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Production Logging Configuration

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict
from pathlib import Path
import json

from config import settings

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging in production
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Create log entry structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'ip_address'):
            log_entry["ip_address"] = record.ip_address
        
        return json.dumps(log_entry, ensure_ascii=False)

class ColoredConsoleFormatter(logging.Formatter):
    """
    Colored console formatter for development
    """
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Format: [LEVEL] timestamp - logger - message
        formatted_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        return f"{log_color}[{record.levelname:8}]{reset_color} {formatted_time} - {record.name} - {record.getMessage()}"

def setup_logging():
    """
    Configure logging based on environment
    """
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Configure formatters based on environment
    if settings.environment == 'production':
        # Production: JSON structured logging
        formatter = StructuredFormatter()
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            logs_dir / f"lumina-{datetime.now().strftime('%Y-%m-%d')}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
        
        # Error file handler for errors only
        error_handler = logging.FileHandler(
            logs_dir / f"lumina-errors-{datetime.now().strftime('%Y-%m-%d')}.log",
            encoding='utf-8'
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # Console handler with JSON for production
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        
    else:
        # Development: Colored console logging
        formatter = ColoredConsoleFormatter()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)
        
        # Optional file handler for development
        if settings.debug:
            file_handler = logging.FileHandler(
                logs_dir / "lumina-dev.log",
                encoding='utf-8'
            )
            simple_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(simple_formatter)
            file_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    
    # Lumina application logger
    lumina_logger = logging.getLogger("lumina")
    lumina_logger.setLevel(log_level)
    
    # Authentication logger
    auth_logger = logging.getLogger("lumina.auth")
    auth_logger.setLevel(log_level)
    
    # OCR processing logger
    ocr_logger = logging.getLogger("lumina.ocr")
    ocr_logger.setLevel(log_level)
    
    # ML processing logger
    ml_logger = logging.getLogger("lumina.ml")
    ml_logger.setLevel(log_level)
    
    # HTTP requests logger
    http_logger = logging.getLogger("lumina.http")
    http_logger.setLevel(log_level)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("easyocr").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    
    # Log startup information
    logger = logging.getLogger("lumina.startup")
    logger.info(f"Logging configured for {settings.environment} environment")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Debug mode: {settings.debug}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    """
    return logging.getLogger(f"lumina.{name}")

# Request logging utility
def log_request(logger: logging.Logger, request, user_id: str = None, extra_data: Dict[str, Any] = None):
    """
    Log HTTP request with structured information
    """
    log_data = {
        "method": request.method,
        "url": str(request.url),
        "user_agent": request.headers.get("user-agent", "Unknown"),
        "ip": request.client.host if request.client else "Unknown",
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if extra_data:
        log_data.update(extra_data)
    
    # Add extra attributes to log record
    extra_attrs = {}
    for key, value in log_data.items():
        extra_attrs[key] = value
    
    logger.info(f"{request.method} {request.url.path}", extra=extra_attrs)

# Error logging utility
def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """
    Log error with context information
    """
    extra_attrs = {}
    if context:
        for key, value in context.items():
            extra_attrs[key] = value
    
    logger.error(f"Error occurred: {str(error)}", exc_info=True, extra=extra_attrs)