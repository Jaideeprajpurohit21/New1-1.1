#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Authentication Routes

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from fastapi.responses import JSONResponse
import logging

from auth import (
    UserCreate, UserLogin, Token, User, UserResponse,
    create_user, authenticate_user, create_access_token, create_session,
    get_emergent_session_data, create_oauth_user, get_current_user, delete_session,
    ACCESS_TOKEN_EXPIRE_DAYS
)

logger = logging.getLogger(__name__)

# Create auth router
auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])

@auth_router.post("/signup", response_model=Token)
async def signup(user_data: UserCreate):
    """Sign up with email and password"""
    try:
        # Create user
        user = await create_user(user_data)
        
        # Create JWT token
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        access_token = create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        # Create session token for cookie-based auth
        session_token = await create_session(user.id)
        
        # Prepare user response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            plan=user.plan,
            created_at=user.created_at
        )
        
        # Create response with session cookie
        response = JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_response.dict()
            }
        )
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 7 days in seconds
            httponly=True,
            secure=True,
            samesite="none",
            path="/"
        )
        
        logger.info(f"User signed up successfully: {user.email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signup"
        )

@auth_router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login with email and password"""
    try:
        # Authenticate user
        user = await authenticate_user(user_credentials.email, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create JWT token
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        access_token = create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        # Create session token for cookie-based auth
        session_token = await create_session(user.id)
        
        # Prepare user response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            plan=user.plan,
            created_at=user.created_at
        )
        
        # Create response with session cookie
        response = JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_response.dict()
            }
        )
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 7 days in seconds
            httponly=True,
            secure=True,
            samesite="none",
            path="/"
        )
        
        logger.info(f"User logged in successfully: {user.email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@auth_router.post("/oauth/session")
async def process_oauth_session(request: Request):
    """Process Emergent OAuth session ID and create user session"""
    try:
        data = await request.json()
        session_id = data.get("session_id")
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID is required"
            )
        
        # Get session data from Emergent
        oauth_data = await get_emergent_session_data(session_id)
        if not oauth_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session ID"
            )
        
        # Create or get user
        user = await create_oauth_user(oauth_data)
        
        # Create session token for cookie-based auth
        session_token = await create_session(user.id)
        
        # Create JWT token
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        access_token = create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        # Prepare user response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            plan=user.plan,
            created_at=user.created_at
        )
        
        # Create response with session cookie
        response = JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_response.dict(),
                "session_token": session_token  # Also return in response for frontend
            }
        )
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 7 days in seconds
            httponly=True,
            secure=True,
            samesite="none",
            path="/"
        )
        
        logger.info(f"OAuth user logged in successfully: {user.email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during OAuth authentication"
        )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        plan=current_user.plan,
        created_at=current_user.created_at
    )

@auth_router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session"""
    try:
        # Get session token from cookie
        session_token = request.cookies.get("session_token")
        if session_token:
            await delete_session(session_token)
        
        # Clear cookie
        response.delete_cookie(
            key="session_token",
            path="/",
            secure=True,
            samesite="none"
        )
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Even if there's an error, clear the cookie
        response.delete_cookie(
            key="session_token",
            path="/",
            secure=True,
            samesite="none"
        )
        return {"message": "Logged out"}