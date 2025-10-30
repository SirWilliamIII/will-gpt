#!/usr/bin/env python3
"""
Search WillGPT Qdrant collection with hybrid retrieval
"""

import sys
import os
from pathlib import Path
import torch
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

# Configuration from .env
QDRANT_URL = os.getenv("QDRANT_URL", "https://79582a58-07be-4684-b371-a80693088b0a.us-east-1-1.aws.cloud.qdrant.io:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "will-gpt")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
MODEL_NAME = "BAAI/bge-m3"
DEVICE = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"


def search_conversations(
    query: str,
    limit: int = 10,
    platform_filter: str = None,
    with_interpretations_only: bool = False,
    date_from: str = None,
    date_to: str = None,
    api_key: str = None,
):
    """
    Search conversations using BGE-M3 embeddings

    Args:
        query: Search query text
        limit: Number of results to return
        platform_filter: Filter by platform (chatgpt, claude)
        with_interpretations_only: Only return chunks with AI interpretations
        date_from: Filter by date (ISO format)
        date_to: Filter by date (ISO format)
        api_key: Qdrant API key
    """

    print("="*70)
    print("WILLGPT HYBRID SEARCH")
    print("="*70)
    print(f"\nQuery: '{query}'")
    print(f"Limit: {limit}")

    # Load model
    print(f"\nLoading BGE-M3 model...")
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)

    # Generate query embedding
    print(f"Generating query embedding...")
    query_embedding = model.encode(query, convert_to_tensor=True)

    # Connect to Qdrant
    print(f"Connecting to Qdrant...")
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=api_key,
        timeout=60,
        prefer_grpc=False,  # Use HTTP REST API
        https=True
    )

    # Build filters
    filters = []

    if platform_filter:
        filters.append(FieldCondition(
            key="platform",
            match=MatchValue(value=platform_filter)
        ))

    if with_interpretations_only:
        filters.append(FieldCondition(
            key="has_interpretations",
            match=MatchValue(value=True)
        ))

    if date_from:
        filters.append(FieldCondition(
            key="timestamp",
            range={
                "gte": date_from
            }
        ))

    if date_to:
        filters.append(FieldCondition(
            key="timestamp",
            range={
                "lte": date_to
            }
        ))

    query_filter = Filter(must=filters) if filters else None

    # Search
    print(f"Searching...")
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=("dense", query_embedding.cpu().tolist()),
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )

    # Display results
    print(f"\n{'='*70}")
    print(f"FOUND {len(results)} RESULTS")
    print(f"{'='*70}\n")

    for i, result in enumerate(results, 1):
        print(f"{'─'*70}")
        print(f"RESULT {i} (score: {result.score:.4f})")
        print(f"{'─'*70}")

        payload = result.payload
        print(f"Title: {payload.get('conversation_title', 'Untitled')}")
        print(f"Platform: {payload.get('platform', 'unknown')}")
        print(f"Date: {payload.get('timestamp', 'unknown')}")
        print(f"Turn: {payload.get('turn_number', 0)}")

        # User message
        user_msg = payload.get('user_message', '')
        if user_msg:
            print(f"\n💬 USER:")
            print(f"   {user_msg[:300]}{'...' if len(user_msg) > 300 else ''}")

        # Assistant message
        assistant_msg = payload.get('assistant_message', '')
        if assistant_msg:
            print(f"\n🤖 ASSISTANT:")
            print(f"   {assistant_msg[:300]}{'...' if len(assistant_msg) > 300 else ''}")

        # AI interpretations
        if payload.get('has_interpretations'):
            print(f"\n🧠 AI INTERPRETATION:")
            about_user = payload.get('about_user', '')
            if about_user:
                print(f"   User: {about_user}")
            about_model = payload.get('about_model', '')
            if about_model:
                print(f"   Model: {about_model}")

        print()

    return results


def interactive_search(api_key: str = None):
    """
    Interactive search loop
    """

    print("\n" + "="*70)
    print("WILLGPT INTERACTIVE SEARCH")
    print("="*70)
    print("\nCommands:")
    print("  /quit - Exit")
    print("  /platform [chatgpt|claude] - Filter by platform")
    print("  /limit [number] - Set result limit")
    print("  /interpretations - Only show chunks with AI interpretations")
    print("  /all - Clear all filters")
    print()

    platform_filter = None
    limit = 10
    with_interpretations = False

    while True:
        try:
            query = input("\n🔍 Query: ").strip()

            if not query:
                continue

            if query == "/quit":
                print("Goodbye!")
                break

            if query.startswith("/platform"):
                parts = query.split()
                if len(parts) > 1:
                    platform_filter = parts[1]
                    print(f"✓ Platform filter set to: {platform_filter}")
                else:
                    platform_filter = None
                    print("✓ Platform filter cleared")
                continue

            if query.startswith("/limit"):
                parts = query.split()
                if len(parts) > 1:
                    limit = int(parts[1])
                    print(f"✓ Limit set to: {limit}")
                continue

            if query == "/interpretations":
                with_interpretations = not with_interpretations
                print(f"✓ Interpretations filter: {with_interpretations}")
                continue

            if query == "/all":
                platform_filter = None
                limit = 10
                with_interpretations = False
                print("✓ All filters cleared")
                continue

            # Execute search
            search_conversations(
                query=query,
                limit=limit,
                platform_filter=platform_filter,
                with_interpretations_only=with_interpretations,
                api_key=api_key,
            )

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


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
        choices=["chatgpt", "claude"],
        help="Filter by platform"
    )
    parser.add_argument(
        "--interpretations",
        action="store_true",
        help="Only show chunks with AI interpretations"
    )
    parser.add_argument(
        "--api-key",
        default=QDRANT_API_KEY,
        help="Qdrant API key (or set QDRANT_API_KEY in .env)"
    )

    args = parser.parse_args()

    if not args.api_key:
        print("❌ Error: QDRANT_API_KEY not found in .env file or --api-key argument")
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
            api_key=args.api_key,
        )
    else:
        # Interactive mode
        interactive_search(api_key=args.api_key)
