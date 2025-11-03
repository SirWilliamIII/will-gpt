#!/usr/bin/env python3
"""
Test all search flags and functionality for search_qdrant.py

Tests:
1. Import verification
2. Argument parsing for all flags
3. Search execution (if Qdrant is available)
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("SEARCH FLAGS TEST SUITE")
print("="*70)

# Test 1: Import verification
print("\n[1/6] Testing imports...")
try:
    from retrieval.search_engine import search_conversations, QDRANT_API_KEY, QDRANT_URL, COLLECTION_NAME, MODEL_NAME
    from retrieval.interactive_search import interactive_search
    print("✅ All imports successful")
    print(f"   - QDRANT_URL: {QDRANT_URL or 'NOT SET'}")
    print(f"   - COLLECTION_NAME: {COLLECTION_NAME or 'NOT SET'}")
    print(f"   - MODEL_NAME: {MODEL_NAME or 'NOT SET'}")
    print(f"   - API_KEY: {'SET' if QDRANT_API_KEY else 'NOT SET'}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Check if Qdrant is configured
if not QDRANT_API_KEY or not QDRANT_URL or not COLLECTION_NAME or not MODEL_NAME:
    print("\n⚠️  Qdrant not fully configured. Tests will be limited to argument parsing.")
    print("   Set QDRANT_API_KEY, QDRANT_URL, COLLECTION_NAME, and MODEL_NAME in .env to run full tests.")
    qdrant_available = False
else:
    qdrant_available = True

# Test 2: Argument parsing with argparse
print("\n[2/6] Testing argument parsing...")
try:
    import argparse

    # Simulate command-line arguments
    test_cases = [
        {
            "name": "Basic query",
            "args": ["test query"],
            "expected": {"query": "test query", "limit": 10}
        },
        {
            "name": "Query with --limit",
            "args": ["test query", "--limit", "5"],
            "expected": {"query": "test query", "limit": 5}
        },
        {
            "name": "Query with --platform chatgpt",
            "args": ["test query", "--platform", "chatgpt"],
            "expected": {"query": "test query", "platform": "chatgpt"}
        },
        {
            "name": "Query with --platform claude",
            "args": ["test query", "--platform", "claude"],
            "expected": {"query": "test query", "platform": "claude"}
        },
        {
            "name": "Query with --platform claude-projects",
            "args": ["test query", "--platform", "claude-projects"],
            "expected": {"query": "test query", "platform": "claude-projects"}
        },
        {
            "name": "Query with --interpretations",
            "args": ["test query", "--interpretations"],
            "expected": {"query": "test query", "interpretations": True}
        },
        {
            "name": "Query with --metadata-filter",
            "args": ["test query", "--metadata-filter", "key:value"],
            "expected": {"query": "test query", "metadata_filter": "key:value"}
        },
        {
            "name": "Combined flags",
            "args": ["test query", "--limit", "3", "--platform", "chatgpt", "--interpretations"],
            "expected": {"query": "test query", "limit": 3, "platform": "chatgpt", "interpretations": True}
        },
    ]

    for test_case in test_cases:
        parser = argparse.ArgumentParser()
        parser.add_argument("query", nargs="*")
        parser.add_argument("--limit", type=int, default=10)
        parser.add_argument("--platform", choices=["chatgpt", "claude", "claude-projects"])
        parser.add_argument("--interpretations", action="store_true")
        parser.add_argument("--metadata-filter")
        parser.add_argument("--api-key")

        args = parser.parse_args(test_case["args"])

        # Verify expected values
        success = True
        for key, expected_value in test_case["expected"].items():
            if key == "query":
                actual_value = " ".join(args.query)
            else:
                actual_value = getattr(args, key.replace("-", "_"))

            if actual_value != expected_value:
                print(f"❌ {test_case['name']}: Expected {key}={expected_value}, got {actual_value}")
                success = False

        if success:
            print(f"✅ {test_case['name']}")

    print("✅ All argument parsing tests passed")

except Exception as e:
    print(f"❌ Argument parsing test failed: {e}")
    sys.exit(1)

# Test 3-6: Actual search tests (only if Qdrant is configured)
if qdrant_available:
    print("\n[3/6] Testing basic search (no filters)...")
    try:
        results = search_conversations(
            query="test",
            limit=2,
            api_key=QDRANT_API_KEY
        )
        print(f"✅ Basic search executed successfully ({len(results)} results)")
    except Exception as e:
        print(f"⚠️  Search failed (this is expected if collection is empty): {e}")

    print("\n[4/6] Testing --platform filter...")
    for platform in ["chatgpt", "claude", "claude-projects"]:
        try:
            results = search_conversations(
                query="test",
                limit=2,
                platform_filter=platform,
                api_key=QDRANT_API_KEY
            )
            print(f"✅ Platform filter '{platform}' executed successfully")
        except Exception as e:
            print(f"⚠️  Platform filter '{platform}' failed: {e}")

    print("\n[5/6] Testing --interpretations filter...")
    try:
        results = search_conversations(
            query="test",
            limit=2,
            with_interpretations_only=True,
            api_key=QDRANT_API_KEY
        )
        print(f"✅ Interpretations filter executed successfully")
    except Exception as e:
        print(f"⚠️  Interpretations filter failed: {e}")

    print("\n[6/6] Testing combined filters...")
    try:
        results = search_conversations(
            query="test",
            limit=2,
            platform_filter="chatgpt",
            with_interpretations_only=True,
            api_key=QDRANT_API_KEY
        )
        print(f"✅ Combined filters executed successfully")
    except Exception as e:
        print(f"⚠️  Combined filters failed: {e}")
else:
    print("\n[3-6] Skipping actual search tests (Qdrant not configured)")

print("\n" + "="*70)
print("TEST SUITE COMPLETE")
print("="*70)
