"""
Custom rate limiting that supports per-API-key limits.
"""

import time
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import HTTPException, Request, status
from api.auth import get_api_key_manager


class PerKeyRateLimiter:
    """Rate limiter that supports different limits per API key."""
    
    def __init__(self):
        # Store: api_key -> (count, window_start_time, limit, period_seconds)
        self.requests: Dict[str, Tuple[int, float, int, int]] = {}
    
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
    
    def check_rate_limit(self, api_key: str, limit_str: str):
        """Check if request is within rate limit for this API key.
        
        Args:
            api_key: The API key
            limit_str: Rate limit string (e.g., '100/minute')
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        limit_count, period_seconds = self._parse_limit(limit_str)
        current_time = time.time()
        
        if api_key in self.requests:
            count, window_start, _, _ = self.requests[api_key]
            
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
                self.requests[api_key] = (count + 1, window_start, limit_count, period_seconds)
            else:
                # New time window
                self.requests[api_key] = (1, current_time, limit_count, period_seconds)
        else:
            # First request for this key
            self.requests[api_key] = (1, current_time, limit_count, period_seconds)
    
    def cleanup_old_entries(self):
        """Remove old entries to prevent memory buildup."""
        current_time = time.time()
        keys_to_remove = []
        
        for api_key, (_, window_start, _, period_seconds) in self.requests.items():
            if current_time - window_start > period_seconds * 2:
                keys_to_remove.append(api_key)
        
        for key in keys_to_remove:
            del self.requests[key]


# Global rate limiter instance
_rate_limiter = PerKeyRateLimiter()


def get_rate_limiter() -> PerKeyRateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


async def check_api_rate_limit(request: Request, api_key: str):
    """Dependency to check rate limit for authenticated requests.
    
    Args:
        request: FastAPI request
        api_key: Validated API key from auth dependency
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    manager = get_api_key_manager()
    rate_limit = manager.get_rate_limit(api_key)
    
    limiter = get_rate_limiter()
    limiter.check_rate_limit(api_key, rate_limit)
