#!/usr/bin/env python3
"""
Merge ChatGPT and Claude conversations and upload to Qdrant

This script:
1. Parses ChatGPT export
2. Parses Claude export
3. Merges both into a single collection
4. Uploads to Qdrant (replacing the collection)
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Validate required environment variables
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY environment variable is required")

QDRANT_URL = os.getenv("QDRANT_URL")
if not QDRANT_URL:
    raise ValueError("QDRANT_URL environment variable is required")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "will-gpt")
MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-m3")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 4))

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parsers import parse_export, ConversationCollection
from parsers.universal_format import UniversalChunk


def merge_and_upload(auto_upload=False):
    """Parse both exports, merge, and upload"""

    print("=" * 70)
    print("WILLGPT MULTI-PLATFORM MERGE & UPLOAD")
    print("=" * 70)

    # Parse ChatGPT
    print("\n1. Parsing ChatGPT export...")
    chatgpt_file = Path("data/raw/chatgpt.json")
    if not chatgpt_file.exists():
        print(f"❌ ChatGPT export not found: {chatgpt_file}")
        sys.exit(1)

    chatgpt_collection = parse_export(str(chatgpt_file))
    print(f"   ✅ Parsed {len(chatgpt_collection.chunks)} ChatGPT chunks")

    # Parse Claude conversations
    print("\n2. Parsing Claude export...")
    claude_file = Path("data/raw/claude.json")
    if not claude_file.exists():
        print(f"❌ Claude export not found: {claude_file}")
        sys.exit(1)

    claude_collection = parse_export(str(claude_file))
    print(f"   ✅ Parsed {len(claude_collection.chunks)} Claude chunks")

    # Parse Claude Projects
    print("\n3. Parsing Claude Projects export...")
    projects_file = Path("data/raw/claude-projects.json")
    if not projects_file.exists():
        print(f"⚠️  Claude Projects export not found: {projects_file}")
        print("   Skipping projects...")
        projects_collection = ConversationCollection(chunks=[])
    else:
        from parsers.claude_projects_parser import ClaudeProjectsParser
        projects_parser = ClaudeProjectsParser()
        projects_collection = projects_parser.parse_export(str(projects_file))
        print(f"   ✅ Parsed {len(projects_collection.chunks)} Claude Projects chunks")

    # Merge collections
    print("\n4. Merging collections...")
    merged_chunks = chatgpt_collection.chunks + claude_collection.chunks + projects_collection.chunks
    merged_collection = ConversationCollection(chunks=merged_chunks)

    total_chunks = len(merged_collection.chunks)
    print(f"   ✅ Merged {total_chunks} total chunks")

    # Platform breakdown
    platform_stats = merged_collection.get_platform_stats()
    print("\n   Platform breakdown:")
    for platform, stats in platform_stats.items():
        print(
            f"     {platform}: {stats['chunk_count']} chunks from {stats['conversation_count']} conversations"
        )

    # Save merged collection
    print("\n5. Saving merged collection...")
    output_path = Path("data/processed/merged_conversations.json")
    merged_collection.save_to_json(
        str(output_path), compact=True, deduplicate_interpretations=True
    )
    print(f"   ✅ Saved to: {output_path}")

    # Upload to Qdrant
    print("\n6. Uploading to Qdrant...")
    print("   This will DELETE the existing collection and recreate it with all data.")

    if not auto_upload:
        response = input("   Continue? (yes/no): ")
        if response.lower() != "yes":
            print("\n❌ Upload cancelled. Merged data saved to:", output_path)
            sys.exit(0)
    else:
        print("   Auto-upload enabled - proceeding...")

    # Import and run upload
    from retrieval.upload_to_qdrant import upload_conversations_to_qdrant

    # Type assertions for Pylance (already validated above)
    assert QDRANT_URL is not None
    assert QDRANT_API_KEY is not None

    upload_conversations_to_qdrant(
        collection_file=str(output_path),
        qdrant_url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
        embedding_mode="user_focused",  # Best for self-effacing pattern detection
        api_key=QDRANT_API_KEY,
        auto_confirm=auto_upload,
    )

    print("\n" + "=" * 70)
    print("✅ MERGE AND UPLOAD COMPLETE!")
    print("=" * 70)
    print(f"Total chunks in Qdrant: {total_chunks}")
    print(f"Platforms: {', '.join(platform_stats.keys())}")
    print("\n🔍 Ready for cross-platform search!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge and upload ChatGPT + Claude conversations"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Auto-confirm upload without prompting"
    )
    args = parser.parse_args()

    merge_and_upload(auto_upload=args.yes)
