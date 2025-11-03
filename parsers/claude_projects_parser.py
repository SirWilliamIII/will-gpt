#!/usr/bin/env python3
"""
Claude Projects Parser
Converts Claude Projects export format to UniversalChunk objects
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from .base_parser import BaseLLMParser, safe_load_json
from .universal_format import UniversalChunk, ConversationCollection


class ClaudeProjectsParser(BaseLLMParser):
    """
    Parser for Claude Projects export files
    
    Claude Projects contain:
    - User memory (conversations_memory field)
    - Project metadata (name, description, prompt_template)
    - Attached documents (docs array)
    
    Strategy: Create 3 types of chunks for optimal retrieval:
    1. User memory chunk (platform-wide context)
    2. Project overview chunks (one per project)
    3. Document chunks (one per document)
    """
    
    def __init__(self):
        super().__init__("claude-projects")
    
    def parse_export(self, file_path: str) -> ConversationCollection:
        """Parse Claude Projects export into UniversalChunk objects"""

        data = safe_load_json(file_path)

        collection = ConversationCollection()
        
        if not isinstance(data, list):
            raise ValueError("Claude Projects export should be a list of projects")
        
        # Process each item
        for item in data:
            # Check if this is the user memory item (first item with conversations_memory)
            if 'conversations_memory' in item:
                chunk = self._create_memory_chunk(item)
                if chunk:
                    collection.add_chunk(chunk)
            else:
                # This is a project
                chunks = self._parse_project(item)
                for chunk in chunks:
                    collection.add_chunk(chunk)
        
        return collection
    
    def _create_memory_chunk(self, memory_item: Dict) -> Optional[UniversalChunk]:
        """Create a chunk from the user memory/context"""
        
        memory_content = memory_item.get('conversations_memory', '')
        account_uuid = memory_item.get('account_uuid', '')
        
        if not memory_content:
            return None
        
        return UniversalChunk(
            chunk_id=str(uuid.uuid4()),
            conversation_id=f"memory_{account_uuid}",
            platform="claude-projects",
            timestamp=datetime.now(),
            
            # Use user_message for the semantic label, assistant_message for content
            user_message="User Context and Memory across all Claude conversations",
            assistant_message=memory_content,
            user_message_type="memory_context",
            assistant_message_type="memory_content",
            
            ai_interpretations={
                "memory_type": "user_context",
                "account_uuid": account_uuid,
                "is_user_memory": True
            },
            system_context={
                "data_type": "conversations_memory"
            },
            
            turn_number=0,
            conversation_title="User Memory",
            raw_metadata={}
        )
    
    def _parse_project(self, project: Dict) -> List[UniversalChunk]:
        """Parse a single project into chunks"""
        
        chunks = []
        
        # Extract project metadata
        project_uuid = project.get('uuid', str(uuid.uuid4()))
        name = project.get('name', 'Untitled Project')
        description = project.get('description', '')
        prompt_template = project.get('prompt_template', '')
        is_private = project.get('is_private', False)
        is_starter = project.get('is_starter_project', False)
        created_at = self._parse_timestamp(project.get('created_at'))
        updated_at = self._parse_timestamp(project.get('updated_at'))
        creator = project.get('creator', {})
        docs = project.get('docs', [])
        
        # Create project overview chunk
        project_chunk = self._create_project_chunk(
            project_uuid, name, description, prompt_template,
            is_private, is_starter, created_at, updated_at, creator
        )
        if project_chunk:
            chunks.append(project_chunk)
        
        # Create document chunks
        for doc in docs:
            doc_chunk = self._create_document_chunk(
                doc, project_uuid, name, created_at
            )
            if doc_chunk:
                chunks.append(doc_chunk)
        
        return chunks
    
    def _create_project_chunk(self, project_uuid: str, name: str, description: str,
                             prompt_template: str, is_private: bool, is_starter: bool,
                             created_at: Optional[datetime], updated_at: Optional[datetime],
                             creator: Dict) -> Optional[UniversalChunk]:
        """Create a chunk for project overview"""
        
        # Build project description
        project_description = f"[PROJECT: {name}]"
        if description:
            project_description += f" {description}"
        
        # Use prompt_template as the "response" content
        project_content = prompt_template if prompt_template else "No custom instructions"
        
        return UniversalChunk(
            chunk_id=str(uuid.uuid4()),
            conversation_id=project_uuid,
            platform="claude-projects",
            timestamp=created_at or datetime.now(),
            
            user_message=project_description,
            assistant_message=project_content,
            user_message_type="project_description",
            assistant_message_type="project_instructions",
            
            ai_interpretations={
                "project_uuid": project_uuid,
                "is_private": is_private,
                "is_starter_project": is_starter,
                "doc_count": 0,  # Will be updated if there are docs
                "content_type": "project_overview"
            },
            system_context={
                "created_at": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None,
                "creator_name": creator.get('full_name', ''),
                "creator_uuid": creator.get('uuid', '')
            },
            
            turn_number=0,
            conversation_title=name,
            raw_metadata={}
        )
    
    def _create_document_chunk(self, doc: Dict, project_uuid: str,
                              project_name: str, project_created_at: Optional[datetime]) -> Optional[UniversalChunk]:
        """Create a chunk for a project document"""
        
        doc_uuid = doc.get('uuid', str(uuid.uuid4()))
        filename = doc.get('filename', 'Untitled Document')
        content = doc.get('content', '')
        doc_created_at = self._parse_timestamp(doc.get('created_at'))
        
        if not content or not content.strip():
            return None
        
        # Build document label
        doc_label = f"[PROJECT: {project_name}] [DOC: {filename}]"
        
        return UniversalChunk(
            chunk_id=str(uuid.uuid4()),
            conversation_id=f"{project_uuid}_doc_{doc_uuid}",
            platform="claude-projects",
            timestamp=doc_created_at or project_created_at or datetime.now(),
            
            user_message=doc_label,
            assistant_message=content,
            user_message_type="document_reference",
            assistant_message_type="document_content",
            
            ai_interpretations={
                "project_uuid": project_uuid,
                "document_uuid": doc_uuid,
                "parent_project": project_name,
                "content_type": "project_document"
            },
            system_context={
                "filename": filename,
                "created_at": doc_created_at.isoformat() if doc_created_at else None
            },
            
            turn_number=0,
            conversation_title=f"{project_name} - {filename}",
            raw_metadata={}
        )
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO timestamp string"""
        
        if not timestamp_str:
            return None
        
        try:
            # Handle ISO format with timezone
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return None
    
    def extract_ai_interpretations(self, raw_data: Dict) -> Dict[str, Any]:
        """Extract project-specific interpretations"""
        
        interpretations = {}
        
        if 'uuid' in raw_data:
            interpretations['project_uuid'] = raw_data['uuid']
        
        if 'is_private' in raw_data:
            interpretations['is_private'] = raw_data['is_private']
        
        if 'is_starter_project' in raw_data:
            interpretations['is_starter_project'] = raw_data['is_starter_project']
        
        return interpretations
    
    def extract_system_context(self, raw_data: Dict) -> Dict[str, Any]:
        """Extract system-level context from project data"""
        
        context = {}
        
        if 'created_at' in raw_data:
            context['created_at'] = raw_data['created_at']
        
        if 'updated_at' in raw_data:
            context['updated_at'] = raw_data['updated_at']
        
        if 'creator' in raw_data:
            context['creator'] = raw_data['creator']
        
        return context
    
    def _validate_data_structure(self, data) -> bool:
        """Validate Claude Projects export structure"""
        
        if not isinstance(data, list):
            return False
        
        if not data:
            return False
        
        # Check if it looks like a projects export
        # Should have either conversations_memory or project structure
        first_item = data[0]
        if isinstance(first_item, dict):
            has_memory = 'conversations_memory' in first_item
            has_project = 'uuid' in first_item and 'name' in first_item
            return has_memory or has_project
        
        return False
    
    def _extract_platform_metadata(self, data) -> Dict[str, Any]:
        """Extract Claude Projects metadata"""
        
        metadata = {
            'format_detected': 'claude_projects_v1',
            'export_format': 'projects_array'
        }
        
        if isinstance(data, list):
            # Count memory items vs projects
            memory_count = sum(1 for item in data if 'conversations_memory' in item)
            project_count = len(data) - memory_count
            
            # Count total documents
            doc_count = sum(
                len(item.get('docs', []))
                for item in data
                if 'docs' in item
            )
            
            metadata['memory_items'] = memory_count
            metadata['total_projects'] = project_count
            metadata['total_documents'] = doc_count
        
        return metadata
