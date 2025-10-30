#!/usr/bin/env python3
"""
Test Qdrant connection and permissions
"""

from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_URL = "https://79582a58-07be-4684-b371-a80693088b0a.us-east-1-1.aws.cloud.qdrant.io:6333"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoyMDc3MTMyMDc2fQ.2kbNJ7tGunrcafxnldpZhmyPXgv689dlfyCQSZ1mYJo"

print("Testing Qdrant connection...")
print(f"URL: {QDRANT_URL}")
print(f"API Key: {API_KEY[:10]}... (length: {len(API_KEY)})")
print()

try:
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=API_KEY,
        timeout=30,
        prefer_grpc=False,  # Use HTTP REST API instead of gRPC
    )
    print("✅ Client created")

    # Test getting collections
    collections = client.get_collections()
    print(f"✅ Successfully connected!")
    print(f"   Collections: {[c.name for c in collections.collections]}")

except Exception as e:
    print(f"❌ Connection failed: {e}")
    print()
    print("Troubleshooting:")
    print("1. Check that the API key is correct in your .env file")
    print("2. Verify the API key has read/write permissions")
    print("3. Confirm the URL matches your Qdrant cluster")
