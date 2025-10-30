#!/usr/bin/env python3
"""
ChatGPT Export Parser
Converts ChatGPT export format to UniversalChunk objects
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from .base_parser import BaseLLMParser
from .universal_format import UniversalChunk, ConversationCollection

class ChatGPTParser(BaseLLMParser):
    """
    Parser for ChatGPT export files
    
    Handles the complex nested UUID tree structure and extracts
    both conversation content and AI interpretations.
    """
    
    def __init__(self):
        super().__init__("chatgpt")
    
    def parse_export(self, file_path: str) -> ConversationCollection:
        """Parse ChatGPT export into UniversalChunk objects"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        
        collection = ConversationCollection()
        
        for conv in conversations:
            chunks = self._parse_conversation(conv)
            for chunk in chunks:
                collection.add_chunk(chunk)
        
        return collection
    
    def _parse_conversation(self, conversation: Dict) -> List[UniversalChunk]:
        """Parse a single ChatGPT conversation into chunks"""
        
        conv_id = conversation.get('conversation_id', str(uuid.uuid4()))
        title = conversation.get('title', 'Untitled')
        mapping = conversation.get('mapping', {})
        
        # Extract messages in chronological order
        messages = self._extract_messages_in_order(mapping)
        
        # Group into conversation chunks (message pairs + context)
        chunks = []
        current_user_msg = None
        current_context = {}
        turn_number = 0
        
        for msg in messages:
            role = msg['role']
            content = msg['content']
            metadata = msg['metadata']
            timestamp = msg['timestamp']
            
            if role == 'system':
                # Collect system interpretations
                if content and content not in current_context.get('system_interpretations', []):
                    if 'system_interpretations' not in current_context:
                        current_context['system_interpretations'] = []
                    current_context['system_interpretations'].append(content)
                    
            elif role == 'user':
                # Start new chunk
                current_user_msg = {
                    'content': content,
                    'message_type': msg['content_type'],
                    'metadata': metadata,
                    'timestamp': timestamp
                }
                
                # Extract user context data (AI's interpretation)
                user_context = metadata.get('user_context_message_data', {})
                if user_context:
                    current_context['user_context_data'] = user_context
                    
            elif role == 'assistant':
                # Complete the chunk
                if current_user_msg:
                    
                    # Extract AI interpretations
                    ai_interpretations = {}
                    if current_context.get('user_context_data'):
                        ai_interpretations['user_context_message_data'] = current_context['user_context_data']
                    
                    # Extract system context
                    system_context = {}
                    if current_context.get('system_interpretations'):
                        system_context['system_interpretations'] = current_context['system_interpretations']
                    
                    # Extract tool usage
                    tool_usage = current_context.get('tool_usage', [])
                    
                    chunk = UniversalChunk(
                        chunk_id=str(uuid.uuid4()),
                        conversation_id=conv_id,
                        platform="chatgpt",
                        timestamp=current_user_msg['timestamp'],
                        
                        user_message=current_user_msg['content'],
                        user_message_type=current_user_msg['message_type'],
                        
                        assistant_message=content,
                        assistant_message_type=msg['content_type'],
                        assistant_model=metadata.get('model_slug'),
                        
                        ai_interpretations=ai_interpretations,
                        system_context=system_context,
                        tool_usage=tool_usage,
                        
                        turn_number=turn_number,
                        has_branches=len(msg.get('children', [])) > 1,
                        conversation_title=title,
                        
                        raw_metadata={
                            'user_metadata': current_user_msg['metadata'],
                            'assistant_metadata': metadata
                        }
                    )
                    
                    chunks.append(chunk)
                    turn_number += 1
                    
                # Reset for next chunk
                current_user_msg = None
                current_context = {
                    'system_interpretations': current_context.get('system_interpretations', []),
                    'user_context_data': current_context.get('user_context_data')
                }
                
            elif role == 'tool':
                # Collect tool usage
                if 'tool_usage' not in current_context:
                    current_context['tool_usage'] = []
                current_context['tool_usage'].append(metadata)
        
        return chunks
    
    def _extract_messages_in_order(self, mapping: Dict) -> List[Dict]:
        """Extract messages from ChatGPT's tree structure in chronological order"""
        
        messages = []
        
        # Find root node (no parent)
        root_id = None
        for msg_id, msg_data in mapping.items():
            if msg_data.get('parent') is None:
                root_id = msg_id
                break
                
        if not root_id:
            return messages
            
        # Traverse the conversation tree
        visited = set()
        self._traverse_conversation_tree(mapping, root_id, messages, visited)
        
        return messages
    
    def _traverse_conversation_tree(self, mapping: Dict, node_id: str, messages: List, visited: set):
        """Recursively traverse ChatGPT's conversation tree"""
        
        if node_id in visited or node_id not in mapping:
            return
            
        visited.add(node_id)
        node = mapping[node_id]
        
        # Extract message if present
        if node.get('message'):
            msg = self._extract_message_data(node['message'])
            if msg:
                messages.append(msg)
        
        # Follow children (main conversation path)
        children = node.get('children', [])
        for child_id in children:
            self._traverse_conversation_tree(mapping, child_id, messages, visited)
    
    def _extract_message_data(self, message: Dict) -> Optional[Dict]:
        """Extract relevant data from a ChatGPT message"""
        
        if not message:
            return None
            
        author = message.get('author', {})
        role = author.get('role', 'unknown')
        
        content_data = message.get('content', {})
        content_type = content_data.get('content_type', 'text')
        
        # Extract actual content
        parts = content_data.get('parts', [])
        content = ''
        if parts:
            # Handle different content types
            if content_type == 'multimodal_text':
                for part in parts:
                    if isinstance(part, dict):
                        content += part.get('text', '')
                    else:
                        content += str(part)
            else:
                content = '\n'.join(str(part) for part in parts if part)
        
        timestamp = message.get('create_time')
        if timestamp:
            timestamp = datetime.fromtimestamp(timestamp)
        
        return {
            'role': role,
            'content': content.strip(),
            'content_type': content_type,
            'metadata': message.get('metadata', {}),
            'timestamp': timestamp,
            'children': message.get('children', [])
        }
    
    def extract_ai_interpretations(self, raw_data: Dict) -> Dict[str, Any]:
        """Extract ChatGPT's interpretation of the user"""
        
        interpretations = {}
        
        # Look for user context message data
        metadata = raw_data.get('metadata', {})
        user_context = metadata.get('user_context_message_data', {})
        
        if user_context:
            interpretations['user_context_message_data'] = user_context
        
        return interpretations
    
    def extract_system_context(self, raw_data: Dict) -> Dict[str, Any]:
        """Extract system prompts and context from ChatGPT data"""
        
        context = {}
        
        # Look for system-level metadata
        metadata = raw_data.get('metadata', {})
        
        # Extract various system indicators
        if metadata.get('is_visually_hidden_from_conversation'):
            context['hidden_from_conversation'] = True
        
        if metadata.get('is_user_system_message'):
            context['user_system_message'] = True
        
        return context
    
    def _validate_data_structure(self, data) -> bool:
        """Validate ChatGPT export structure"""
        
        if not isinstance(data, list):
            return False
        
        if not data:
            return True  # Empty export is valid
        
        # Check first conversation structure
        first_conv = data[0]
        required_keys = ['mapping']
        
        for key in required_keys:
            if key not in first_conv:
                return False
        
        # Check mapping structure
        mapping = first_conv['mapping']
        if not isinstance(mapping, dict):
            return False
        
        # Look for UUID-style keys
        for key in mapping.keys():
            if len(key) == 36 and key.count('-') == 4:  # UUID format
                return True
        
        return False
    
    def _extract_platform_metadata(self, data) -> Dict[str, Any]:
        """Extract ChatGPT-specific metadata"""
        
        if not isinstance(data, list) or not data:
            return {}
        
        total_conversations = len(data)
        total_messages = 0
        date_range = [None, None]
        models_used = set()
        has_interpretations = 0
        has_tool_usage = 0
        
        for conv in data:
            mapping = conv.get('mapping', {})
            
            for msg_id, msg_data in mapping.items():
                message = msg_data.get('message')
                if message:
                    total_messages += 1
                    
                    # Track date range
                    create_time = message.get('create_time')
                    if create_time:
                        dt = datetime.fromtimestamp(create_time)
                        if date_range[0] is None or dt < date_range[0]:
                            date_range[0] = dt
                        if date_range[1] is None or dt > date_range[1]:
                            date_range[1] = dt
                    
                    # Track models
                    model = message.get('metadata', {}).get('model_slug')
                    if model:
                        models_used.add(model)
                    
                    # Track interpretations
                    user_context = message.get('metadata', {}).get('user_context_message_data')
                    if user_context:
                        has_interpretations += 1
                    
                    # Track tool usage
                    if 'search_result_groups' in message.get('metadata', {}):
                        has_tool_usage += 1
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'date_range': date_range,
            'models_used': list(models_used),
            'messages_with_interpretations': has_interpretations,
            'messages_with_tool_usage': has_tool_usage
        }
