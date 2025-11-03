#!/usr/bin/env python3
"""
Interactive search interface for WillGPT conversations
"""

from typing import Optional
from .search_engine import search_conversations


def interactive_search(api_key: Optional[str] = None):
    """
    Interactive search loop with command interface.

    Commands:
        /quit - Exit interactive mode
        /platform [chatgpt|claude|claude-projects] - Filter by platform
        /limit [number] - Set result limit
        /interpretations - Toggle AI interpretations filter
        /metadata <key>:<value> - Filter by metadata
        /all - Clear all filters

    Args:
        api_key: Qdrant API key (optional, uses env var if not provided)
    """

    print("\n" + "="*70)
    print("WILLGPT INTERACTIVE SEARCH")
    print("="*70)
    print("\nCommands:")
    print("  /quit - Exit")
    print("  /platform [chatgpt|claude|claude-projects] - Filter by platform")
    print("  /limit [number] - Set result limit")
    print("  /interpretations - Only show chunks with AI interpretations")
    print("  /metadata <key>:<value> - Filter by metadata")
    print("  /all - Clear all filters")
    print()

    # Search state
    platform_filter = None
    limit = 10
    with_interpretations = False
    metadata_filter = None

    while True:
        try:
            query = input("\n🔍 Query: ").strip()

            if not query:
                continue

            # Command: Quit
            if query == "/quit":
                print("Goodbye!")
                break

            # Command: Platform filter
            if query.startswith("/platform"):
                parts = query.split()
                if len(parts) > 1:
                    platform_filter = parts[1]
                    print(f"✓ Platform filter set to: {platform_filter}")
                else:
                    platform_filter = None
                    print("✓ Platform filter cleared")
                continue

            # Command: Limit
            if query.startswith("/limit"):
                parts = query.split()
                if len(parts) > 1:
                    limit = int(parts[1])
                    print(f"✓ Limit set to: {limit}")
                continue

            # Command: Interpretations toggle
            if query == "/interpretations":
                with_interpretations = not with_interpretations
                print(f"✓ Interpretations filter: {with_interpretations}")
                continue

            # Command: Metadata filter
            if query.startswith("/metadata"):
                parts = query.split(" ", 1)
                if len(parts) > 1:
                    metadata_filter = parts[1]
                    print(f"✓ Metadata filter set to: {metadata_filter}")
                else:
                    metadata_filter = None
                    print("✓ Metadata filter cleared")
                continue

            # Command: Clear all filters
            if query == "/all":
                platform_filter = None
                limit = 10
                with_interpretations = False
                metadata_filter = None
                print("✓ All filters cleared")
                continue

            # Execute search with current filters
            search_conversations(
                query=query,
                limit=limit,
                platform_filter=platform_filter,
                with_interpretations_only=with_interpretations,
                metadata_filter=metadata_filter,
                api_key=api_key,
            )

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
