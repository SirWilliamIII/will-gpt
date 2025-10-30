#!/usr/bin/env python3
"""
Test the parser framework with your existing ChatGPT export
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from parsers import parse_export, get_export_metadata, compare_ai_interpretations

def test_parser(export_file_path: str):
    """Test the parser framework with an actual export file"""
    
    print("="*60)
    print("TESTING WILLGPT PARSER FRAMEWORK")
    print("="*60)
    
    # Test 1: Get metadata
    print("\n1. EXPORT METADATA ANALYSIS")
    print("-" * 40)
    
    try:
        metadata = get_export_metadata(export_file_path)
        for key, value in metadata.items():
            print(f"{key}: {value}")
    except Exception as e:
        print(f"Metadata extraction failed: {e}")
        return
    
    # Test 2: Parse conversations
    print("\n2. PARSING CONVERSATIONS")
    print("-" * 40)
    
    try:
        collection = parse_export(export_file_path)
        print(f"Successfully parsed {len(collection.chunks)} conversation chunks")
        
        # Platform stats
        print(f"Platforms: {collection.get_platforms()}")
        print(f"Date range: {collection.get_date_range()}")
        
        platform_stats = collection.get_platform_stats()
        for platform, stats in platform_stats.items():
            print(f"\n{platform.upper()} STATS:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
    
    except Exception as e:
        print(f"Parsing failed: {e}")
        return
    
    # Test 3: Sample chunks
    print("\n3. SAMPLE CONVERSATION CHUNKS")
    print("-" * 40)
    
    try:
        for i, chunk in enumerate(collection.chunks[:3]):
            print(f"\nCHUNK {i+1}:")
            print(f"Platform: {chunk.platform}")
            print(f"Timestamp: {chunk.timestamp}")
            print(f"Title: {chunk.conversation_title}")
            
            if chunk.user_message:
                print(f"User: {chunk.user_message[:100]}...")
            
            if chunk.assistant_message:
                print(f"Assistant: {chunk.assistant_message[:100]}...")
            
            if chunk.ai_interpretations:
                print(f"AI Interpretations: {chunk.ai_interpretations}")
            
            if chunk.tool_usage:
                print(f"Tool Usage: {len(chunk.tool_usage)} tool calls")
            
            print(f"\nEmbedding text preview:")
            embedding_text = chunk.to_embedding_text()
            print(embedding_text[:200] + "...")
            print("-" * 40)
    
    except Exception as e:
        print(f"Chunk analysis failed: {e}")
    
    # Test 4: Save processed data
    print("\n4. SAVING PROCESSED DATA")
    print("-" * 40)
    
    try:
        output_path = project_root / "data" / "processed_conversations.json"
        collection.save_to_json(str(output_path))
        print(f"Saved processed data to: {output_path}")
        
        # Test loading
        loaded_collection = collection.load_from_json(str(output_path))
        print(f"Verified: Loaded {len(loaded_collection.chunks)} chunks")
    
    except Exception as e:
        print(f"Save/load failed: {e}")
    
    print("\n" + "="*60)
    print("PARSER FRAMEWORK TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_parser.py <path_to_export_file>")
        print("Example: python test_parser.py ~/conversations.json")
        sys.exit(1)
    
    export_file = sys.argv[1]
    
    if not os.path.exists(export_file):
        print(f"Error: File not found: {export_file}")
        sys.exit(1)
    
    test_parser(export_file)
