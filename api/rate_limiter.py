"""
Custom rate limiting that supports per-API-key limits and IP-based limits.
"""

import time
import os
from typing import Dict, Tuple, Optional
from fastapi import HTTPException, Request, status
from api.auth import get_api_key_manager


class PerKeyRateLimiter:
    """Rate limiter that supports different limits per API key and IP address."""
    
    def __init__(self):
        # Store: api_key -> (count, window_start_time, limit, period_seconds)
        self.api_key_requests: Dict[str, Tuple[int, float, int, int]] = {}
        # Store: ip_address -> (count, window_start_time, limit, period_seconds)
        self.ip_requests: Dict[str, Tuple[int, float, int, int]] = {}
    
    def _parse_limit(self, limit_str: str) -> Tuple[int, int]:
        """Parse rate limit string like '100/minute' into (count, seconds).
        
        Args:
            limit_str: Rate limit string (e.g., '100/minute', '1000/hour')
            
        Returns:
            Tuple of (request_count, period_in_seconds)
        """
        try:
            count_str, period = limit_str.split('/')
            count = int(count_str)
            
            period_map = {
                'second': 1,
                'minute': 60,
                'hour': 3600,
                'day': 86400
            }
            
            seconds = period_map.get(period.lower(), 60)
            return count, seconds
        except (ValueError, KeyError):
            # Default to 100/minute if parsing fails
            return 100, 60
    
    def _check_limit(self, identifier: str, limit_str: str, storage: Dict):
        """Generic rate limit checking for any identifier.
        
        Args:
            identifier: Unique identifier (API key or IP address)
            limit_str: Rate limit string
            storage: The storage dict to use (api_key_requests or ip_requests)
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        limit_count, period_seconds = self._parse_limit(limit_str)
        current_time = time.time()
        
        if identifier in storage:
            count, window_start, _, _ = storage[identifier]
            
            # Check if we're still in the same time window
            if current_time - window_start < period_seconds:
                if count >= limit_count:
                    # Rate limit exceeded
                    retry_after = int(period_seconds - (current_time - window_start))
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded: {limit_str}",
                        headers={"Retry-After": str(retry_after)}
                    )
                # Increment counter
                storage[identifier] = (count + 1, window_start, limit_count, period_seconds)
            else:
                # New time window
                storage[identifier] = (1, current_time, limit_count, period_seconds)
        else:
            # First request for this identifier
            storage[identifier] = (1, current_time, limit_count, period_seconds)
    
    def check_rate_limit(self, api_key: str, limit_str: str):
        """Check if request is within rate limit for this API key.
        
        Args:
            api_key: The API key
            limit_str: Rate limit string (e.g., '100/minute')
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        self._check_limit(api_key, limit_str, self.api_key_requests)
    
    def check_ip_rate_limit(self, ip_address: str, limit_str: str):
        """Check if request is within rate limit for this IP address.
        
        Args:
            ip_address: The client IP address
            limit_str: Rate limit string (e.g., '100/minute')
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        self._check_limit(ip_address, limit_str, self.ip_requests)
    
    def cleanup_old_entries(self):
        """Remove old entries to prevent memory buildup."""
        current_time = time.time()
        
        # Cleanup API key requests
        keys_to_remove = []
        for api_key, (_, window_start, _, period_seconds) in self.api_key_requests.items():
            if current_time - window_start > period_seconds * 2:
                keys_to_remove.append(api_key)
        for key in keys_to_remove:
            del self.api_key_requests[key]
        
        # Cleanup IP requests
        ips_to_remove = []
        for ip, (_, window_start, _, period_seconds) in self.ip_requests.items():
            if current_time - window_start > period_seconds * 2:
                ips_to_remove.append(ip)
        for ip in ips_to_remove:
            del self.ip_requests[ip]


# Global rate limiter instance
_rate_limiter = PerKeyRateLimiter()


def get_rate_limiter() -> PerKeyRateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


async def check_api_rate_limit(api_key: Optional[str], request: Request):
    """Dependency to check rate limit for authenticated requests.
    
    Args:
        api_key: Validated API key from auth dependency (None if auth is disabled)
        request: FastAPI request
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    limiter = get_rate_limiter()
    
    # Check IP-based rate limit first (applies to all requests)
    ip_limit = os.getenv('IP_RATE_LIMIT', None)
    if ip_limit:
        client_ip = request.client.host if request.client else '0.0.0.0'
        limiter.check_ip_rate_limit(client_ip, ip_limit)
    
    # Then check API key-specific rate limit (only if API key auth is enabled)
    if api_key is not None:
        manager = get_api_key_manager()
        rate_limit = manager.get_rate_limit(api_key)
        limiter.check_rate_limit(api_key, rate_limit)


async def check_ip_rate_limit_only(request: Request):
    """Dependency to check IP rate limit for public endpoints.
    
    Args:
        request: FastAPI request
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    ip_limit = os.getenv('IP_RATE_LIMIT', '1000/hour')
    client_ip = request.client.host if request.client else '0.0.0.0'
    
    limiter = get_rate_limiter()
    limiter.check_ip_rate_limit(client_ip, ip_limit)
