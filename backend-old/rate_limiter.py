#!/usr/bin/env python3
"""
LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
Rate Limiting System

Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict, deque
from fastapi import HTTPException, Request, status
from logging_config import get_logger

logger = get_logger("rate_limiter")

class RateLimiter:
    """
    In-memory rate limiter with sliding window algorithm
    """
    
    def __init__(self):
        # Store request timestamps per user per endpoint
        self._requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self._cleanup_interval = 300  # Cleanup every 5 minutes
        self._last_cleanup = time.time()
    
    def _cleanup_old_requests(self):
        """
        Remove old request records to prevent memory leaks
        """
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Keep records for 1 hour
        
        for user_id in list(self._requests.keys()):
            for endpoint in list(self._requests[user_id].keys()):
                # Remove timestamps older than cutoff
                while (self._requests[user_id][endpoint] and 
                       self._requests[user_id][endpoint][0] < cutoff_time):
                    self._requests[user_id][endpoint].popleft()
                
                # Remove empty endpoint records
                if not self._requests[user_id][endpoint]:
                    del self._requests[user_id][endpoint]
            
            # Remove empty user records
            if not self._requests[user_id]:
                del self._requests[user_id]
        
        self._last_cleanup = current_time
        logger.debug("Rate limiter cleanup completed")
    
    def _get_rate_limit_key(self, user_id: str, endpoint: str) -> str:
        """
        Generate rate limit key for user and endpoint
        """
        return f"{user_id}:{endpoint}"
    
    def check_rate_limit(self, user_id: str, endpoint: str, limit: int, window_minutes: int = 1) -> bool:
        """
        Check if request is within rate limit
        
        Args:
            user_id: User identifier
            endpoint: API endpoint identifier
            limit: Number of requests allowed
            window_minutes: Time window in minutes
            
        Returns:
            True if within limit, False otherwise
        """
        current_time = time.time()
        window_seconds = window_minutes * 60
        cutoff_time = current_time - window_seconds
        
        # Clean up old requests periodically
        self._cleanup_old_requests()
        
        # Get user's requests for this endpoint
        requests = self._requests[user_id][endpoint]
        
        # Remove requests outside the time window
        while requests and requests[0] < cutoff_time:
            requests.popleft()
        
        # Check if limit exceeded
        if len(requests) >= limit:
            logger.warning(
                f"Rate limit exceeded for user {user_id} on endpoint {endpoint}",
                extra={
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "limit": limit,
                    "window_minutes": window_minutes,
                    "requests_count": len(requests)
                }
            )
            return False
        
        # Add current request timestamp
        requests.append(current_time)
        
        logger.debug(
            f"Rate limit check passed for user {user_id} on endpoint {endpoint}",
            extra={
                "user_id": user_id,
                "endpoint": endpoint,
                "requests_count": len(requests),
                "limit": limit
            }
        )
        
        return True
    
    def get_rate_limit_info(self, user_id: str, endpoint: str, limit: int, window_minutes: int = 1) -> Dict[str, int]:
        """
        Get rate limit information for user and endpoint
        """
        current_time = time.time()
        window_seconds = window_minutes * 60
        cutoff_time = current_time - window_seconds
        
        # Get current requests count
        requests = self._requests[user_id][endpoint]
        
        # Remove requests outside the time window
        while requests and requests[0] < cutoff_time:
            requests.popleft()
        
        remaining = max(0, limit - len(requests))
        reset_time = int(current_time + window_seconds) if requests else int(current_time)
        
        return {
            "limit": limit,
            "remaining": remaining,
            "used": len(requests),
            "reset_time": reset_time
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(user_id: str, endpoint: str, limit: int, window_minutes: int = 1):
    """
    Rate limit decorator function
    """
    if not rate_limiter.check_rate_limit(user_id, endpoint, limit, window_minutes):
        # Get rate limit info for headers
        info = rate_limiter.get_rate_limit_info(user_id, endpoint, limit, window_minutes)
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Maximum {limit} requests per {window_minutes} minute(s) allowed",
                "retry_after": window_minutes * 60,
                "limit": info["limit"],
                "remaining": info["remaining"],
                "reset_time": info["reset_time"]
            },
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": str(info["remaining"]),
                "X-RateLimit-Reset": str(info["reset_time"]),
                "Retry-After": str(window_minutes * 60)
            }
        )

def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request
    """
    # Check for forwarded headers (for proxy/load balancer scenarios)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP if multiple are present
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"

def create_rate_limit_dependency(endpoint: str, limit: int, window_minutes: int = 1):
    """
    Create a dependency function for rate limiting specific endpoints
    """
    def rate_limit_dependency(request: Request, current_user = None):
        # Use user ID if authenticated, otherwise use IP address
        identifier = current_user.id if current_user else get_client_ip(request)
        
        check_rate_limit(identifier, endpoint, limit, window_minutes)
        
        # Add rate limit info to response headers (will be handled by middleware)
        info = rate_limiter.get_rate_limit_info(identifier, endpoint, limit, window_minutes)
        request.state.rate_limit_info = info
    
    return rate_limit_dependency