#!/usr/bin/env python3
"""Generate a CallShield API key.

Usage:
    python scripts/generate_api_key.py --name "my-app"
"""

import argparse
import json
import os
import secrets
from datetime import datetime, timezone

KEYS_FILE = os.path.join(os.path.dirname(__file__), "..", "backend", "api_keys.json")


def load_keys(path: str) -> dict:
    """Load existing keys or return empty dict."""
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        return {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def generate_key() -> str:
    """Generate a prefixed API key: cs_<32 hex chars>."""
    return f"cs_{secrets.token_hex(16)}"


def main():
    parser = argparse.ArgumentParser(description="Generate a CallShield API key")
    parser.add_argument("--name", required=True, help="Name/label for this key (e.g. 'my-app')")
    args = parser.parse_args()

    keys = load_keys(KEYS_FILE)
    key = generate_key()

    keys[key] = {
        "name": args.name,
        "created": datetime.now(timezone.utc).isoformat(),
        "active": True,
    }

    os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

    print(f"\nAPI key generated successfully!\n")
    print(f"  Key:  {key}")
    print(f"  Name: {args.name}")
    print(f"  File: {os.path.abspath(KEYS_FILE)}\n")
    print(f"Usage example:\n")
    print(f'  curl -X POST http://localhost:8000/api/analyze/transcript \\')
    print(f'    -H "Content-Type: application/json" \\')
    print(f'    -H "X-API-Key: {key}" \\')
    print(f'    -d \'{{"transcript": "Hello, this is a test."}}\'\n')


if __name__ == "__main__":
    main()
