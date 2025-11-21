#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Production Configuration Module

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # MongoDB Configuration
    mongodb_uri: str = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    db_name: str = os.getenv('DB_NAME', 'lumina_db')
    
    # JWT Configuration
    jwt_secret: str = os.getenv('JWT_SECRET', 'fallback-secret-change-in-production')
    jwt_algorithm: str = 'HS256'
    jwt_expire_days: int = 7
    
    # Server Configuration
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', 8000))
    
    # CORS Configuration
    frontend_origin: str = os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000')
    
    # Environment
    environment: str = os.getenv('ENVIRONMENT', 'development')
    debug: bool = environment == 'development'
    
    # File Upload Configuration
    uploads_dir: Path = Path('uploads')
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    
    # Allowed file extensions
    allowed_extensions: set = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}
    
    class Config:
        env_file = '.env'
        case_sensitive = False

# Global settings instance
settings = Settings()

# Ensure uploads directory exists
settings.uploads_dir.mkdir(exist_ok=True)