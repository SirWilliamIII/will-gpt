#!/usr/bin/env python3
"""
Claude Export Parser
Converts Claude export format to UniversalChunk objects
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from .base_parser import BaseLLMParser
from .universal_format import UniversalChunk, ConversationCollection

class ClaudeParser(BaseLLMParser):
    """
    Parser for Claude export files
    
    Note: This is a placeholder implementation until we see the actual
    Claude export format. Will be updated when fresh exports arrive.
    """
    
    def __init__(self):
        super().__init__("claude")
    
    def parse_export(self, file_path: str) -> ConversationCollection:
        """Parse Claude export into UniversalChunk objects"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        collection = ConversationCollection()
        
        # TODO: Implement based on actual Claude export format
        # This is a placeholder that will be updated when we see real data
        
        if isinstance(data, list):
            # Assume list of conversations
            for conv in data:
                chunks = self._parse_conversation(conv)
                for chunk in chunks:
                    collection.add_chunk(chunk)
        elif isinstance(data, dict):
            # Assume single conversation or wrapper object
            if 'conversations' in data:
                for conv in data['conversations']:
                    chunks = self._parse_conversation(conv)
                    for chunk in chunks:
                        collection.add_chunk(chunk)
            else:
                chunks = self._parse_conversation(data)
                for chunk in chunks:
                    collection.add_chunk(chunk)
        
        return collection
    
    def _parse_conversation(self, conversation: Dict) -> List[UniversalChunk]:
        """Parse a single Claude conversation into chunks"""
        
        # Placeholder implementation - update when we see real format
        conv_id = conversation.get('id', str(uuid.uuid4()))
        title = conversation.get('title', 'Untitled')
        
        chunks = []
        
        # Look for different possible message structures
        messages = (conversation.get('messages', []) or 
                   conversation.get('turns', []) or
                   conversation.get('exchanges', []))
        
        turn_number = 0
        
        for i in range(0, len(messages), 2):
            # Assume alternating user/assistant pattern
            user_msg = messages[i] if i < len(messages) else None
            assistant_msg = messages[i + 1] if i + 1 < len(messages) else None
            
            if user_msg and assistant_msg:
                chunk = self._create_chunk_from_messages(
                    user_msg, assistant_msg, conv_id, title, turn_number
                )
                if chunk:
                    chunks.append(chunk)
                    turn_number += 1
        
        return chunks
    
    def _create_chunk_from_messages(self, user_msg: Dict, assistant_msg: Dict, 
                                   conv_id: str, title: str, turn_number: int) -> Optional[UniversalChunk]:
        """Create a UniversalChunk from user and assistant messages"""
        
        # Extract user message
        user_content = self._extract_message_content(user_msg)
        user_timestamp = self._extract_timestamp(user_msg)
        
        # Extract assistant message  
        assistant_content = self._extract_message_content(assistant_msg)
        
        if not user_content or not assistant_content:
            return None
        
        # Look for Claude-specific interpretation data
        ai_interpretations = self.extract_ai_interpretations(assistant_msg)
        system_context = self.extract_system_context(user_msg)
        
        return UniversalChunk(
            chunk_id=str(uuid.uuid4()),
            conversation_id=conv_id,
            platform="claude",
            timestamp=user_timestamp or datetime.now(),
            
            user_message=user_content,
            user_message_type=user_msg.get('type', 'text'),
            
            assistant_message=assistant_content,
            assistant_message_type=assistant_msg.get('type', 'text'),
            
            ai_interpretations=ai_interpretations,
            system_context=system_context,
            
            turn_number=turn_number,
            conversation_title=title,
            
            raw_metadata={
                'user_raw': user_msg,
                'assistant_raw': assistant_msg
            }
        )
    
    def _extract_message_content(self, message: Dict) -> str:
        """Extract content from a Claude message"""
        
        # Try different possible content fields
        content = (message.get('content') or 
                  message.get('text') or
                  message.get('message') or
                  message.get('body', ''))
        
        if isinstance(content, list):
            # Handle content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    text_parts.append(block.get('text', ''))
                else:
                    text_parts.append(str(block))
            return '\n'.join(text_parts)
        
        return str(content)
    
    def _extract_timestamp(self, message: Dict) -> Optional[datetime]:
        """Extract timestamp from Claude message"""
        
        # Try different timestamp fields
        timestamp_fields = ['timestamp', 'created_at', 'date', 'time']
        
        for field in timestamp_fields:
            if field in message:
                timestamp = message[field]
                
                if isinstance(timestamp, (int, float)):
                    return datetime.fromtimestamp(timestamp)
                elif isinstance(timestamp, str):
                    try:
                        # Try ISO format
                        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        continue
        
        return None
    
    def extract_ai_interpretations(self, raw_data: Dict) -> Dict[str, Any]:
        """Extract Claude's interpretation of the user"""
        
        interpretations = {}
        
        # Look for Claude-specific interpretation fields
        # This will be updated when we see actual Claude export format
        
        metadata = raw_data.get('metadata', {})
        
        # Look for thinking/reasoning traces
        if 'thinking' in raw_data:
            interpretations['thinking'] = raw_data['thinking']
        
        # Look for model reasoning
        if 'reasoning' in metadata:
            interpretations['reasoning'] = metadata['reasoning']
        
        # Look for user modeling
        if 'user_model' in metadata:
            interpretations['user_model'] = metadata['user_model']
        
        return interpretations
    
    def extract_system_context(self, raw_data: Dict) -> Dict[str, Any]:
        """Extract system prompts and context from Claude data"""
        
        context = {}
        
        # Look for system prompts
        if raw_data.get('role') == 'system':
            context['system_prompt'] = raw_data.get('content', '')
        
        # Look for other system-level metadata
        metadata = raw_data.get('metadata', {})
        
        if 'system_instructions' in metadata:
            context['system_instructions'] = metadata['system_instructions']
        
        return context
    
    def _validate_data_structure(self, data) -> bool:
        """Validate Claude export structure"""
        
        # This is a placeholder - will be updated when we see real format
        
        if isinstance(data, list):
            if not data:
                return True
            
            # Check if it looks like a conversation list
            first_item = data[0]
            if isinstance(first_item, dict):
                # Look for conversation-like fields
                conversation_fields = ['messages', 'turns', 'exchanges', 'id', 'title']
                if any(field in first_item for field in conversation_fields):
                    return True
        
        elif isinstance(data, dict):
            # Single conversation or wrapper
            conversation_fields = ['messages', 'turns', 'exchanges', 'conversations']
            if any(field in data for field in conversation_fields):
                return True
        
        return False
    
    def _extract_platform_metadata(self, data) -> Dict[str, Any]:
        """Extract Claude-specific metadata"""
        
        # Placeholder implementation
        metadata = {
            'format_detected': 'claude_placeholder',
            'needs_implementation': True
        }
        
        if isinstance(data, list):
            metadata['total_conversations'] = len(data)
        elif isinstance(data, dict):
            if 'conversations' in data:
                metadata['total_conversations'] = len(data['conversations'])
            else:
                metadata['total_conversations'] = 1
        
        return metadata
