#!/usr/bin/env python3
"""
API Key Generator for Malaysia Postcodes API.

Usage:
    python api/key_generator.py [--name CLIENT_NAME]
"""

import secrets
import json
import sys
from pathlib import Path
from datetime import datetime
import argparse


def generate_api_key() -> str:
    """Generate a secure random API key.
    
    Returns:
        64-character hexadecimal API key
    """
    return secrets.token_hex(32)


def add_api_key(keys_file: str = "api_keys.json", client_name: str = None, rate_limit: str = None):
    """Add a new API key to the keys file.
    
    Args:
        keys_file: Path to the API keys file
        client_name: Name/description for the client
        rate_limit: Rate limit for this key (e.g., '100/minute', '1000/hour')
    """
    keys_path = Path(keys_file)
    
    # Load existing keys or create new structure
    if keys_path.exists():
        with open(keys_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"keys": []}
        keys_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate new key
    new_key = generate_api_key()
    
    # Add to keys list
    key_entry = {
        "key": new_key,
        "name": client_name or f"Client-{len(data['keys']) + 1}",
        "created": datetime.now().isoformat(),
        "rate_limit": rate_limit or "100/minute"
    }
    
    data['keys'].append(key_entry)
    
    # Save back to file
    with open(keys_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Generated new API key for: {key_entry['name']}")
    print(f"✓ Created: {key_entry['created']}")
    print(f"✓ Rate Limit: {key_entry['rate_limit']}")
    print(f"\n{'='*70}")
    print(f"API Key: {new_key}")
    print(f"{'='*70}")
    print(f"\nThis key has been saved to: {keys_file}")
    print(f"Total keys: {len(data['keys'])}")
    print(f"\nUsage:")
    print(f"  curl -H 'X-API-Key: {new_key}' http://localhost:8000/states")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate API keys for Malaysia Postcodes API"
    )
    parser.add_argument(
        '--name',
        type=str,
        help='Name/description for the client (e.g., "Production App", "Test Client")'
    )
    parser.add_argument(
        '--rate-limit',
        type=str,
        help='Rate limit for this key (e.g., "100/minute", "1000/hour", "5000/day"). Default: 100/minute'
    )
    parser.add_argument(
        '--file',
        type=str,
        default='api_keys.json',
        help='Path to API keys file (default: api_keys.json)'
    )
    
    args = parser.parse_args()
    
    try:
        add_api_key(keys_file=args.file, client_name=args.name, rate_limit=args.rate_limit)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
