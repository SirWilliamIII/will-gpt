#!/usr/bin/env python3
"""
Search WillGPT Qdrant collection with hybrid retrieval

Main entry point for searching conversations. Provides both:
- Single query mode: python search_qdrant.py "your query"
- Interactive mode: python search_qdrant.py

Split into modules:
- search_engine.py: Core search functionality
- interactive_search.py: Interactive CLI interface
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import search functions
from retrieval.search_engine import search_conversations
from retrieval.interactive_search import interactive_search

# Environment variables
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search WillGPT Qdrant collection")
    parser.add_argument(
        "query",
        nargs="*",
        help="Search query (leave empty for interactive mode)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of results (default: 10)"
    )
    parser.add_argument(
        "--platform",
        choices=["chatgpt", "claude", "claude-projects"],
        help="Filter by platform"
    )
    parser.add_argument(
        "--interpretations",
        action="store_true",
        help="Only show chunks with AI interpretations"
    )
    parser.add_argument(
        "--metadata-filter",
        help="Filter by metadata in the format key:value"
    )
    parser.add_argument(
        "--api-key",
        default=QDRANT_API_KEY,
        help="Qdrant API key (or set QDRANT_API_KEY in .env)"
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: QDRANT_API_KEY not found in .env file or --api-key argument")
        print("   Add QDRANT_API_KEY to your .env file or pass --api-key")
        sys.exit(1)

    if args.query:
        # Single query mode
        query = " ".join(args.query)
        search_conversations(
            query=query,
            limit=args.limit,
            platform_filter=args.platform,
            with_interpretations_only=args.interpretations,
            metadata_filter=args.metadata_filter,
            api_key=args.api_key
        )
    else:
        # Interactive mode
        interactive_search(api_key=args.api_key)
