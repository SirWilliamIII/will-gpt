#!/usr/bin/env python3
"""
Claude Export Parser
Converts Claude export format to UniversalChunk objects
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from .base_parser import BaseLLMParser, safe_load_json
from .universal_format import UniversalChunk, ConversationCollection

class ClaudeParser(BaseLLMParser):
    """
    Parser for Claude export files

    Handles Claude's conversation export format which consists of:
    - Array of conversations with uuid, name, chat_messages
    - Messages with sender field (human/assistant)
    - ISO timestamp format
    """

    def __init__(self):
        super().__init__("claude")
    
    def parse_export(self, file_path: str) -> ConversationCollection:
        """Parse Claude export into UniversalChunk objects"""

        data = safe_load_json(file_path)

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

        conv_id = conversation.get('uuid', str(uuid.uuid4()))
        title = conversation.get('name', 'Untitled')

        chunks = []

        # Claude uses 'chat_messages' array with 'sender' field
        messages = conversation.get('chat_messages', [])

        turn_number = 0
        i = 0

        # Iterate through messages, pairing human with assistant
        while i < len(messages):
            # Find next human message
            user_msg = None
            while i < len(messages) and messages[i].get('sender') == 'human':
                user_msg = messages[i]
                i += 1
                break  # Take first human message

            # Find corresponding assistant message
            assistant_msg = None
            if i < len(messages) and messages[i].get('sender') == 'assistant':
                assistant_msg = messages[i]
                i += 1

            # Create chunk if we have both messages
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

            raw_metadata={}  # Removed bloated metadata (saves ~114 MB)
        )
    
    def _extract_message_content(self, message: Dict) -> Optional[str]:
        """Extract content from a Claude message"""

        # Primary: use 'text' field directly
        text = message.get('text', '').strip()

        # If text is empty, try parsing content array
        if not text:
            content = message.get('content', [])
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        block_text = block.get('text', '').strip()
                        if block_text:
                            text_parts.append(block_text)
                text = '\n'.join(text_parts)

        # Skip empty messages (similar to ChatGPT optimization)
        if not text:
            return None

        return text
    
    def _extract_timestamp(self, message: Dict) -> Optional[datetime]:
        """Extract timestamp from Claude message"""

        # Claude uses 'created_at' field with ISO format
        timestamp_str = message.get('created_at', '')

        if timestamp_str:
            try:
                # Parse ISO format: "2024-06-20T23:33:34.483665Z"
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                # Fallback: try as unix timestamp
                try:
                    return datetime.fromtimestamp(float(timestamp_str))
                except:
                    pass

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

        if isinstance(data, list):
            if not data:
                return False

            # Check if it looks like a Claude conversation list
            first_item = data[0]
            if isinstance(first_item, dict):
                # Claude conversations have: uuid, name, chat_messages
                required_fields = ['uuid', 'chat_messages']
                if all(field in first_item for field in required_fields):
                    return True

        return False
    
    def _extract_platform_metadata(self, data) -> Dict[str, Any]:
        """Extract Claude-specific metadata"""

        metadata: Dict[str, Any] = {
            'format_detected': 'claude_export_v1',
            'export_format': 'conversation_array'
        }

        if isinstance(data, list):
            metadata['total_conversations'] = len(data)
            metadata['total_messages'] = sum(
                len(conv.get('chat_messages', []))
                for conv in data
            )

        return metadata
