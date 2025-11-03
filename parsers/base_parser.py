#!/usr/bin/env python3
"""
Base Parser Interface
All platform parsers inherit from this
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
import json

from .universal_format import UniversalChunk, ConversationCollection

# Maximum file size to load (500 MB default, adjustable)
MAX_FILE_SIZE_MB = 500


def safe_load_json(file_path: str, max_size_mb: int = MAX_FILE_SIZE_MB) -> Any:
    """
    Safely load JSON file with size validation to prevent memory exhaustion.

    Args:
        file_path: Path to JSON file
        max_size_mb: Maximum file size in MB (default: 500 MB)

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If file is too large or cannot be parsed
    """
    file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)

    if file_size_mb > max_size_mb:
        raise ValueError(
            f"File {file_path} is too large ({file_size_mb:.1f} MB). "
            f"Maximum allowed: {max_size_mb} MB. "
            f"This prevents memory exhaustion attacks."
        )

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading {file_path}: {e}")

class BaseLLMParser(ABC):
    """
    Abstract base class for all LLM platform parsers
    
    Each platform (ChatGPT, Claude, etc.) implements this interface
    to convert their export format into UniversalChunk objects.
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
    
    @abstractmethod
    def parse_export(self, file_path: str) -> ConversationCollection:
        """
        Parse platform export file into UniversalChunk objects
        
        Args:
            file_path: Path to the export file
            
        Returns:
            ConversationCollection with parsed chunks
        """
        pass
    
    @abstractmethod
    def extract_ai_interpretations(self, raw_data: Dict) -> Dict[str, Any]:
        """
        Extract AI's interpretation/understanding of user from raw data
        
        This is platform-specific - ChatGPT has user context data,
        Claude might have different interpretation structures.
        
        Args:
            raw_data: Raw conversation data from export
            
        Returns:
            Dictionary of AI interpretations
        """
        pass
    
    @abstractmethod
    def extract_system_context(self, raw_data: Dict) -> Dict[str, Any]:
        """
        Extract system prompts, instructions, context from raw data
        
        Args:
            raw_data: Raw conversation data from export
            
        Returns:
            Dictionary of system context
        """
        pass
    
    def validate_export_format(self, file_path: str) -> bool:
        """
        Validate that the file is in the expected format for this parser

        Args:
            file_path: Path to export file

        Returns:
            True if format is valid, False otherwise
        """
        try:
            data = safe_load_json(file_path)
            return self._validate_data_structure(data)
        except Exception:
            return False
    
    @abstractmethod
    def _validate_data_structure(self, data) -> bool:
        """Platform-specific validation logic"""
        pass
    
    def get_export_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata about the export (date range, conversation count, etc.)

        Args:
            file_path: Path to export file

        Returns:
            Dictionary with export metadata
        """
        file_size = Path(file_path).stat().st_size / 1024 / 1024  # MB

        try:
            data = safe_load_json(file_path)

            metadata = {
                'platform': self.platform_name,
                'file_size_mb': round(file_size, 1),
                'export_structure': type(data).__name__,
            }

            # Platform-specific metadata extraction
            metadata.update(self._extract_platform_metadata(data))

            return metadata

        except Exception as e:
            return {
                'platform': self.platform_name,
                'file_size_mb': round(file_size, 1),
                'error': str(e)
            }
    
    @abstractmethod  
    def _extract_platform_metadata(self, data) -> Dict[str, Any]:
        """Extract platform-specific metadata"""
        pass

class ParserRegistry:
    """
    Registry for all available parsers
    Automatically detects which parser to use for a given export file
    """
    
    def __init__(self):
        self.parsers = {}
    
    def register_parser(self, parser_class: type, file_extensions: List[str] = None):
        """
        Register a parser for specific file types
        
        Args:
            parser_class: Parser class inheriting from BaseLLMParser
            file_extensions: List of file extensions this parser handles
        """
        parser_instance = parser_class()
        self.parsers[parser_instance.platform_name] = {
            'parser': parser_instance,
            'extensions': file_extensions or ['.json']
        }
    
    def detect_parser(self, file_path: str) -> BaseLLMParser:
        """
        Automatically detect which parser to use for a file
        
        Args:
            file_path: Path to export file
            
        Returns:
            Appropriate parser instance
            
        Raises:
            ValueError: If no suitable parser found
        """
        file_ext = Path(file_path).suffix.lower()
        
        # Try each parser's validation method
        for platform_name, parser_info in self.parsers.items():
            parser = parser_info['parser']
            
            if file_ext in parser_info['extensions']:
                if parser.validate_export_format(file_path):
                    print(f"Detected {platform_name} export format")
                    return parser
        
        # Fallback: try all parsers regardless of extension
        for platform_name, parser_info in self.parsers.items():
            parser = parser_info['parser']
            if parser.validate_export_format(file_path):
                print(f"Detected {platform_name} export format (by content)")
                return parser
        
        raise ValueError(f"No suitable parser found for {file_path}")
    
    def parse_export(self, file_path: str) -> ConversationCollection:
        """
        Parse any export file using automatic detection
        
        Args:
            file_path: Path to export file
            
        Returns:
            ConversationCollection with parsed chunks
        """
        parser = self.detect_parser(file_path)
        return parser.parse_export(file_path)
    
    def get_all_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata from all parsers (useful for comparison)"""
        metadata = {}
        
        for platform_name, parser_info in self.parsers.items():
            try:
                parser = parser_info['parser']
                metadata[platform_name] = parser.get_export_metadata(file_path)
            except Exception as e:
                metadata[platform_name] = {'error': str(e)}
        
        return metadata

# Global parser registry instance
parser_registry = ParserRegistry()
