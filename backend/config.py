#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Production Configuration Module

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import os
import secrets
from typing import Optional, List, Set
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from pathlib import Path

class Settings(BaseSettings):
    """
    Comprehensive application settings loaded from environment variables
    """
    
    # =====================
    # Database Configuration
    # =====================
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017/",
        description="MongoDB connection URI"
    )
    db_name: str = Field(
        default="lumina_db",
        description="Database name"
    )
    mongodb_timeout: int = Field(
        default=10000,
        description="MongoDB connection timeout in milliseconds"
    )
    
    # =====================
    # JWT Configuration
    # =====================
    jwt_secret: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="JWT secret key for token signing"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    jwt_expire_days: int = Field(
        default=7,
        description="JWT token expiration in days"
    )
    
    @validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT secret must be at least 32 characters long')
        return v
    
    # =====================
    # Server Configuration
    # =====================
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        description="Server port"
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload for development"
    )
    
    # =====================
    # CORS Configuration
    # =====================
    frontend_origin: str = Field(
        default="http://localhost:3000",
        description="Allowed frontend origin for CORS"
    )
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="List of allowed CORS origins"
    )
    
    # =====================
    # Environment
    # =====================
    environment: str = Field(
        default="development",
        description="Application environment (development/production)"
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    @validator('debug', pre=True, always=True)
    def set_debug_mode(cls, v, values):
        if 'environment' in values:
            return values['environment'] == 'development'
        return v
    
    # =====================
    # File Upload Configuration
    # =====================
    uploads_dir: Path = Field(
        default=Path("uploads"),
        description="Directory for uploaded files"
    )
    max_upload_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file upload size in bytes"
    )
    allowed_extensions: Set[str] = Field(
        default={'.jpg', '.jpeg', '.png', '.pdf'},
        description="Allowed file extensions"
    )
    
    # =====================
    # Rate Limiting Configuration
    # =====================
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    upload_rate_limit: int = Field(
        default=10,
        description="Upload requests per minute per user"
    )
    api_rate_limit: int = Field(
        default=100,
        description="General API requests per minute per user"
    )
    
    # =====================
    # Security Configuration
    # =====================
    allowed_hosts: List[str] = Field(
        default_factory=list,
        description="Allowed hosts for security"
    )
    secure_cookies: bool = Field(
        default=False,
        description="Use secure cookies (HTTPS only)"
    )
    
    @validator('secure_cookies', pre=True, always=True)
    def set_secure_cookies(cls, v, values):
        if 'environment' in values:
            return values['environment'] == 'production'
        return v
    
    # =====================
    # OCR Configuration
    # =====================
    ocr_timeout: int = Field(
        default=30,
        description="OCR processing timeout in seconds"
    )
    ocr_gpu: bool = Field(
        default=False,
        description="Use GPU for OCR processing"
    )
    
    # =====================
    # ML Configuration
    # =====================
    ml_model_path: Path = Field(
        default=Path("models"),
        description="Path to ML models"
    )
    ml_confidence_threshold: float = Field(
        default=0.7,
        description="ML prediction confidence threshold"
    )
    
    # =====================
    # Monitoring Configuration
    # =====================
    health_check_timeout: int = Field(
        default=30,
        description="Health check timeout in seconds"
    )
    metrics_enabled: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    
    # =====================
    # Stripe Configuration
    # =====================
    stripe_api_key: str = Field(
        default="sk_test_emergent",
        description="Stripe API key for payment processing"
    )
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False
        validate_assignment = True
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.uploads_dir.mkdir(exist_ok=True, parents=True)
        self.ml_model_path.mkdir(exist_ok=True, parents=True)
        
        # Set allowed origins from frontend_origin
        if self.frontend_origin not in self.allowed_origins:
            self.allowed_origins.append(self.frontend_origin)

# Global settings instance
settings = Settings()