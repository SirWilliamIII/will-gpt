#!/usr/bin/env python3
"""
Parser Package Initialization
Auto-registers all available parsers
"""

from .universal_format import UniversalChunk, ConversationCollection
from .base_parser import BaseLLMParser, ParserRegistry, parser_registry
from .chatgpt_parser import ChatGPTParser
from .claude_parser import ClaudeParser
from .claude_projects_parser import ClaudeProjectsParser

# Auto-register all parsers
parser_registry.register_parser(ChatGPTParser, ['.json'])
parser_registry.register_parser(ClaudeParser, ['.json'])
parser_registry.register_parser(ClaudeProjectsParser, ['.json'])

# Convenience functions
def parse_export(file_path: str) -> ConversationCollection:
    """
    Parse any LLM export file automatically
    
    Args:
        file_path: Path to export file
        
    Returns:
        ConversationCollection with parsed chunks
    """
    return parser_registry.parse_export(file_path)

def get_export_metadata(file_path: str) -> dict:
    """
    Get metadata about an export file
    
    Args:
        file_path: Path to export file
        
    Returns:
        Dictionary with export metadata
    """
    parser = parser_registry.detect_parser(file_path)
    return parser.get_export_metadata(file_path)

def compare_ai_interpretations(chunks, pattern: str) -> dict:
    """
    Compare how different AIs interpreted the same user pattern
    
    Args:
        chunks: List of UniversalChunk objects or ConversationCollection
        pattern: Pattern to search for in user messages
        
    Returns:
        Dictionary comparing interpretations across platforms
    """
    from .universal_format import compare_ai_interpretations
    
    if hasattr(chunks, 'chunks'):
        chunks = chunks.chunks
    
    return compare_ai_interpretations(chunks, pattern)

__all__ = [
    'UniversalChunk',
    'ConversationCollection', 
    'BaseLLMParser',
    'ChatGPTParser',
    'ClaudeParser',
    'ClaudeProjectsParser',
    'parser_registry',
    'parse_export',
    'get_export_metadata',
    'compare_ai_interpretations'
]
