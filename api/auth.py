"""
API Key authentication for the Malaysia Postcodes API.
"""

import json
import os
from typing import Dict, List, Optional, Set
from datetime import datetime
from pathlib import Path

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader


# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyManager:
    """Manages API keys for authentication."""
    
    def __init__(self, keys_file: str = "api_keys.json"):
        """Initialize API key manager.
        
        Args:
            keys_file: Path to the JSON file containing API keys
        """
        self.keys_file = keys_file
        self.valid_keys: Set[str] = set()
        self.key_info: Dict[str, Dict] = {}  # key -> {name, created}
        
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from file."""
        keys_path = Path(self.keys_file)
        
        if not keys_path.exists():
            print(f"Warning: API keys file not found: {self.keys_file}")
            print("Creating empty keys file. Generate keys using: python api/key_generator.py")
            self._create_empty_keys_file()
            return
        
        try:
            with open(keys_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            keys = data.get('keys', [])
            for key_entry in keys:
                key = key_entry.get('key')
                if key:
                    self.valid_keys.add(key)
                    self.key_info[key] = {
                        'name': key_entry.get('name', 'Unknown'),
                        'created': key_entry.get('created', 'Unknown'),
                        'rate_limit': key_entry.get('rate_limit', os.getenv('RATE_LIMIT', '100/minute'))
                    }
            
            print(f"Loaded {len(self.valid_keys)} API key(s) from {self.keys_file}")
        
        except json.JSONDecodeError as e:
            print(f"Error parsing API keys file: {e}")
            raise
    
    def _create_empty_keys_file(self):
        """Create an empty API keys file with example structure."""
        keys_path = Path(self.keys_file)
        keys_path.parent.mkdir(parents=True, exist_ok=True)
        
        empty_data = {
            "keys": []
        }
        
        with open(keys_path, 'w', encoding='utf-8') as f:
            json.dump(empty_data, f, indent=2)
    
    def validate_key(self, api_key: str) -> bool:
        """Validate an API key.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        return api_key in self.valid_keys
    
    def get_key_info(self, api_key: str) -> Optional[Dict]:
        """Get information about an API key.
        
        Args:
            api_key: The API key
            
        Returns:
            Dictionary with key info or None if not found
        """
        return self.key_info.get(api_key)
    
    def get_rate_limit(self, api_key: str) -> str:
        """Get rate limit for an API key.
        
        Args:
            api_key: The API key
            
        Returns:
            Rate limit string (e.g., '100/minute')
        """
        key_info = self.key_info.get(api_key)
        if key_info:
            return key_info.get('rate_limit', os.getenv('RATE_LIMIT', '100/minute'))
        return os.getenv('RATE_LIMIT', '100/minute')


# Global instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get the global APIKeyManager instance.
    
    Returns:
        APIKeyManager instance
        
    Raises:
        RuntimeError: If manager hasn't been initialized
    """
    global _api_key_manager
    if _api_key_manager is None:
        raise RuntimeError("API key manager not initialized.")
    return _api_key_manager


def load_api_keys(keys_file: str = "api_keys.json"):
    """Load API keys into global manager.
    
    Args:
        keys_file: Path to the JSON file containing API keys
    """
    global _api_key_manager
    _api_key_manager = APIKeyManager(keys_file)


async def verify_api_key(api_key: str = Security(api_key_header)) -> Optional[str]:
    """Verify API key from request header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        The validated API key, or None if authentication is disabled
        
    Raises:
        HTTPException: If API key is required but missing or invalid (401)
    """
    # Check if API key authentication is required
    require_api_key = os.getenv("REQUIRE_API_KEY", "true").lower() == "true"
    
    if not require_api_key:
        # Authentication disabled, return None to indicate no API key
        return None
    
    # Authentication required
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )
    
    manager = get_api_key_manager()
    if not manager.validate_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return api_key


def get_api_key_identifier(api_key: str) -> str:
    """Get a unique identifier for rate limiting based on API key.
    
    Args:
        api_key: The API key
        
    Returns:
        Identifier string for rate limiting
    """
    return f"api_key:{api_key}"
