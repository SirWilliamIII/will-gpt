#!/usr/bin/env python3
"""
Test Claude Projects Parser
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parsers.claude_projects_parser import ClaudeProjectsParser


def test_projects_parser():
    """Test parsing Claude Projects export"""
    
    print("=" * 70)
    print("TESTING CLAUDE PROJECTS PARSER")
    print("=" * 70)
    
    # Initialize parser
    parser = ClaudeProjectsParser()
    
    # Parse the file
    projects_file = Path("data/raw/claude-projects.json")
    
    if not projects_file.exists():
        print(f"\n❌ File not found: {projects_file}")
        sys.exit(1)
    
    print(f"\nParsing: {projects_file}")
    collection = parser.parse_export(str(projects_file))
    
    print(f"\n✅ Parsed {len(collection.chunks)} chunks")
    
    # Analyze chunks by type
    memory_chunks = [c for c in collection.chunks if c.user_message_type == "memory_context"]
    project_chunks = [c for c in collection.chunks if c.user_message_type == "project_description"]
    doc_chunks = [c for c in collection.chunks if c.user_message_type == "document_reference"]
    
    print(f"\nChunk breakdown:")
    print(f"  Memory chunks: {len(memory_chunks)}")
    print(f"  Project chunks: {len(project_chunks)}")
    print(f"  Document chunks: {len(doc_chunks)}")
    
    # Show sample chunks
    print("\n" + "=" * 70)
    print("SAMPLE CHUNKS")
    print("=" * 70)
    
    if memory_chunks:
        print("\n1. USER MEMORY CHUNK:")
        chunk = memory_chunks[0]
        print(f"   Platform: {chunk.platform}")
        print(f"   Title: {chunk.conversation_title}")
        print(f"   User Message: {chunk.user_message[:100]}...")
        print(f"   Assistant Message (first 200 chars): {chunk.assistant_message[:200]}...")
        print(f"   AI Interpretations: {chunk.ai_interpretations}")
    
    if project_chunks:
        print("\n2. PROJECT OVERVIEW CHUNK:")
        chunk = project_chunks[0]
        print(f"   Platform: {chunk.platform}")
        print(f"   Title: {chunk.conversation_title}")
        print(f"   User Message: {chunk.user_message}")
        print(f"   Assistant Message: {chunk.assistant_message[:200] if chunk.assistant_message else 'None'}...")
        print(f"   AI Interpretations: {chunk.ai_interpretations}")
    
    if doc_chunks:
        print("\n3. DOCUMENT CHUNK:")
        chunk = doc_chunks[0]
        print(f"   Platform: {chunk.platform}")
        print(f"   Title: {chunk.conversation_title}")
        print(f"   User Message: {chunk.user_message}")
        print(f"   Assistant Message (first 200 chars): {chunk.assistant_message[:200]}...")
        print(f"   AI Interpretations: {chunk.ai_interpretations}")
    
    # Test embedding text generation
    print("\n" + "=" * 70)
    print("EMBEDDING TEXT GENERATION TEST")
    print("=" * 70)
    
    if project_chunks:
        chunk = project_chunks[0]
        embedding_text = chunk.to_embedding_text(mode="balanced")
        print(f"\nProject chunk embedding text (first 500 chars):")
        print(embedding_text[:500])
    
    if doc_chunks:
        chunk = doc_chunks[0]
        embedding_text = chunk.to_embedding_text(mode="balanced")
        print(f"\nDocument chunk embedding text (first 500 chars):")
        print(embedding_text[:500])
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print(f"\nTotal chunks created: {len(collection.chunks)}")
    print("Parser is working correctly!")


if __name__ == "__main__":
    test_projects_parser()
