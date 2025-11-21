#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Authentication Module with JWT and Emergent Google OAuth

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import secrets
import re
from fastapi import HTTPException, status, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr, validator
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import aiohttp
from bson import ObjectId

logger = logging.getLogger(__name__)

# Import production configuration
from config import settings

# JWT Configuration
SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_DAYS = settings.jwt_expire_days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security for optional auth header (don't use HTTPAuthorizationCredentials as it breaks cookie auth)
security = HTTPBearer(auto_error=False)

# User Models
class UserBase(BaseModel):
    email: EmailStr
    name: str = ""
    picture: str = ""
    plan: str = "free"
    stripe_customer_id: Optional[str] = None
    stripe_subscription_status: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str = ""
    
    @validator('password')
    def validate_password(cls, v):
        """Strong password validation: 8+ chars, uppercase, lowercase, numbers, special chars"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str = Field(alias="_id")
    hashed_password: Optional[str] = None
    created_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    plan: str
    created_at: datetime

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Database connection (will be set from main server.py)
db = None

def set_database(database):
    """Set the database connection from main server"""
    global db
    db = database

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Session utilities for Emergent auth
async def create_session(user_id: str) -> str:
    """Create a session token and store in database"""
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    session_data = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.user_sessions.insert_one(session_data)
    return session_token

async def get_user_by_session(session_token: str) -> Optional[User]:
    """Get user by session token"""
    # Find session
    session = await db.user_sessions.find_one({
        "session_token": session_token,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not session:
        return None
    
    # Find user
    user_doc = await db.users.find_one({"_id": session["user_id"]})
    if not user_doc:
        return None
    
    # Convert ObjectId to string for Pydantic
    user_doc["id"] = str(user_doc["_id"])
    return User(**user_doc)

async def delete_session(session_token: str):
    """Delete a session token"""
    await db.user_sessions.delete_one({"session_token": session_token})

# Emergent OAuth utilities
async def get_emergent_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session data from Emergent OAuth service"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"X-Session-ID": session_id}
            async with session.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Emergent auth failed: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error calling Emergent auth: {str(e)}")
        return None

# User CRUD operations
async def create_user(user_data: UserCreate) -> User:
    """Create a new user with email/password"""
    # Check if user already exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_doc = {
        "_id": str(ObjectId()),
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": get_password_hash(user_data.password),
        "picture": "",
        "plan": "free",
        "stripe_customer_id": None,
        "stripe_subscription_status": None,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(user_doc)
    user_doc["id"] = user_doc["_id"]
    return User(**user_doc)

async def create_oauth_user(oauth_data: Dict[str, Any]) -> User:
    """Create or get user from OAuth data"""
    # Check if user already exists
    existing = await db.users.find_one({"email": oauth_data["email"]})
    if existing:
        # Return existing user, don't update data
        existing["id"] = str(existing["_id"])
        return User(**existing)
    
    # Create new user
    user_doc = {
        "_id": str(ObjectId()),
        "email": oauth_data["email"],
        "name": oauth_data.get("name", ""),
        "picture": oauth_data.get("picture", ""),
        "plan": "free",
        "stripe_customer_id": None,
        "stripe_subscription_status": None,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(user_doc)
    user_doc["id"] = user_doc["_id"]
    return User(**user_doc)

async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user_doc = await db.users.find_one({"email": email})
    if not user_doc:
        return None
    
    if not user_doc.get("hashed_password"):
        # OAuth user, no password
        return None
    
    if not verify_password(password, user_doc["hashed_password"]):
        return None
    
    user_doc["id"] = str(user_doc["_id"])
    return User(**user_doc)

# Auth dependencies
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Get current authenticated user from session token (cookie) or Authorization header"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try session token from cookie first
    session_token = request.cookies.get("session_token")
    if session_token:
        user = await get_user_by_session(session_token)
        if user:
            return user
    
    # Fallback to Authorization header
    if credentials and credentials.credentials:
        # Check if it's a JWT token
        payload = verify_token(credentials.credentials)
        if payload:
            user_id = payload.get("sub")
            if user_id:
                user_doc = await db.users.find_one({"_id": user_id})
                if user_doc:
                    user_doc["id"] = str(user_doc["_id"])
                    return User(**user_doc)
        
        # Check if it's a session token
        user = await get_user_by_session(credentials.credentials)
        if user:
            return user
    
    raise credentials_exception

# Optional auth dependency (doesn't raise exception)
async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current authenticated user, return None if not authenticated"""
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None