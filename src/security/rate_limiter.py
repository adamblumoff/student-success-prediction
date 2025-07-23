#!/usr/bin/env python3
"""
Rate limiting utilities
"""

import time
from collections import defaultdict, deque
from typing import Dict, Tuple
from fastapi import HTTPException, Request, status
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        # Store request timestamps per client
        self.clients: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Rate limit configurations (requests per time window)
        self.limits = {
            'default': (100, 3600),      # 100 requests per hour
            'upload': (10, 3600),        # 10 file uploads per hour
            'analysis': (50, 3600),      # 50 analysis requests per hour
            'auth': (5, 300),            # 5 auth attempts per 5 minutes
        }
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Try to get real IP from headers (if behind proxy)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.client.host if request.client else 'unknown'
        
        # Include user agent for additional uniqueness
        user_agent = request.headers.get('user-agent', 'unknown')[:50]
        return f"{client_ip}:{hash(user_agent) % 10000}"
    
    def _clean_old_requests(self, client_requests: deque, window_seconds: int) -> None:
        """Remove requests older than window"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        while client_requests and client_requests[0] < cutoff_time:
            client_requests.popleft()
    
    def check_rate_limit(self, request: Request, limit_type: str = 'default') -> bool:
        """Check if request is within rate limit"""
        if limit_type not in self.limits:
            limit_type = 'default'
        
        max_requests, window_seconds = self.limits[limit_type]
        client_id = self._get_client_id(request)
        client_requests = self.clients[client_id]
        
        # Clean old requests
        self._clean_old_requests(client_requests, window_seconds)
        
        # Check if limit exceeded
        if len(client_requests) >= max_requests:
            logger.warning(f"Rate limit exceeded for client {client_id}: "
                         f"{len(client_requests)}/{max_requests} in {window_seconds}s")
            return False
        
        # Add current request
        client_requests.append(time.time())
        return True
    
    def enforce_rate_limit(self, request: Request, limit_type: str = 'default') -> None:
        """Enforce rate limit or raise HTTP exception"""
        if not self.check_rate_limit(request, limit_type):
            max_requests, window_seconds = self.limits[limit_type]
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.",
                headers={
                    "Retry-After": str(window_seconds),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Window": str(window_seconds)
                }
            )
    
    def get_rate_limit_info(self, request: Request, limit_type: str = 'default') -> Dict[str, int]:
        """Get current rate limit information for client"""
        if limit_type not in self.limits:
            limit_type = 'default'
        
        max_requests, window_seconds = self.limits[limit_type]
        client_id = self._get_client_id(request)
        client_requests = self.clients[client_id]
        
        # Clean old requests
        self._clean_old_requests(client_requests, window_seconds)
        
        current_requests = len(client_requests)
        remaining_requests = max(0, max_requests - current_requests)
        
        # Calculate reset time
        if client_requests:
            oldest_request = client_requests[0]
            reset_time = int(oldest_request + window_seconds)
        else:
            reset_time = int(time.time() + window_seconds)
        
        return {
            'limit': max_requests,
            'remaining': remaining_requests,
            'reset': reset_time,
            'window': window_seconds
        }
    
    def update_limits(self, new_limits: Dict[str, Tuple[int, int]]) -> None:
        """Update rate limit configurations"""
        self.limits.update(new_limits)
    
    def clear_client(self, client_id: str) -> None:
        """Clear rate limit data for specific client"""
        if client_id in self.clients:
            del self.clients[client_id]
    
    def get_stats(self) -> Dict[str, int]:
        """Get rate limiter statistics"""
        total_clients = len(self.clients)
        total_requests = sum(len(requests) for requests in self.clients.values())
        
        return {
            'total_clients': total_clients,
            'total_active_requests': total_requests,
            'limits_configured': len(self.limits)
        }

# Global instance
rate_limiter = RateLimiter()

# FastAPI middleware function
async def rate_limit_middleware(request: Request, limit_type: str = 'default'):
    """Middleware to enforce rate limiting"""
    rate_limiter.enforce_rate_limit(request, limit_type)
    return rate_limiter.get_rate_limit_info(request, limit_type)