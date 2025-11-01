#!/usr/bin/env python3
"""
Test Qdrant connection and permissions
"""

from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
MODEL_NAME = os.getenv("MODEL_NAME")

print("Testing Qdrant connection...")
print(f"URL: {QDRANT_URL}")
if QDRANT_API_KEY is not None:
    print(f"API Key: {QDRANT_API_KEY[:10]}... (length: {len(QDRANT_API_KEY)})")
else:
    print("API Key: None")
print()

try:
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
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
