#!/usr/bin/env python3
"""
Universal Conversation Chunk Format
Standard data structure for all LLM platforms

EMBEDDING STRATEGY FOR BGE-M3:
------------------------------
Based on analysis of ChatGPT exports (1,327 conversations, 13,139 chunks):
- AI interpretations are mostly STATIC (only 2 unique interpretations across 7,337 chunks)
- Primary signal for self-effacing patterns: USER MESSAGES
- Secondary signal: ASSISTANT RESPONSES (reflect AI's treatment based on its model)
- Tertiary signal: AI INTERPRETATIONS (useful for cross-platform comparison)

Recommended embedding modes:
1. "balanced" (default): User + truncated assistant + interpretations (~400 tokens avg)
   - Best for general retrieval with context
   - Works well with BGE-M3's hybrid approach

2. "user_focused": User message + AI interpretations only
   - Best for finding specific user patterns (self-effacing, topics, behaviors)
   - Minimizes noise from long assistant responses

3. "minimal": User message only
   - For pure semantic clustering of user statements
   - Fastest embedding generation

4. "full": Everything including full responses
   - For complete conversation context
   - May exceed optimal token length (avg ~1600 chars)

BGE-M3 produces three embedding types from one forward pass:
- Dense vectors: Semantic similarity
- Sparse vectors: Keyword/lexical matching (benefits from structured markers like [TOPIC:])
- ColBERT multi-vectors: Token-level fine-grained matching
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid
import json

@dataclass
class UniversalChunk:
    """
    Standard conversation chunk format across all LLM platforms
    
    This is the unified format that all platform parsers output,
    enabling cross-platform analysis and retrieval.
    """
    
    # Core identifiers
    chunk_id: str
    conversation_id: str
    platform: str  # "chatgpt", "claude", etc.
    
    # Timestamps
    timestamp: datetime
    conversation_start: Optional[datetime] = None
    
    # Core content
    user_message: Optional[str] = None
    assistant_message: Optional[str] = None
    user_message_type: Optional[str] = None
    assistant_message_type: Optional[str] = None
    
    # The gold: AI interpretations and metadata
    ai_interpretations: Dict[str, Any] = None  # Platform's model of user
    system_context: Dict[str, Any] = None     # System prompts, context
    tool_usage: List[Dict] = None             # Search, function calls, etc.
    
    # Conversation flow
    turn_number: int = 0
    has_branches: bool = False
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = None
    
    # Content metadata
    conversation_title: str = "Untitled"
    user_confidence: Optional[str] = None     # If detected
    assistant_model: Optional[str] = None     # gpt-4, claude-3, etc.
    
    # Raw platform data (for debugging/analysis)
    raw_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.ai_interpretations is None:
            self.ai_interpretations = {}
        if self.system_context is None:
            self.system_context = {}
        if self.tool_usage is None:
            self.tool_usage = []
        if self.child_chunk_ids is None:
            self.child_chunk_ids = []
        if self.raw_metadata is None:
            self.raw_metadata = {}
    
    def to_embedding_text(self,
                          mode: str = "balanced",
                          max_assistant_chars: int = 3000,
                          include_interpretations: bool = True,
                          include_title: bool = True) -> str:
        """
        Generate text for BGE-M3 hybrid embeddings optimized for finding self-effacing patterns.

        Based on analysis: ChatGPT interpretations are mostly static across conversations,
        so the primary signal comes from user messages and assistant responses.

        Args:
            mode: Embedding strategy
                - "balanced": User + truncated assistant + interpretations (default, ~400 tokens avg)
                - "user_focused": Just user message + AI interpretations (best for pattern finding)
                - "full": Everything including full assistant response (may exceed optimal length)
                - "minimal": User message only (for dense semantic clustering)
            max_assistant_chars: Max characters from assistant (default 3000 ≈ 750 tokens)
            include_interpretations: Include AI's model of user (static for ChatGPT)
            include_title: Include conversation title for topic context

        Returns:
            Formatted text optimized for BGE-M3's dense/sparse/ColBERT embeddings
        """
        parts = []

        # Topic context (helps BGE-M3's sparse embeddings cluster by subject)
        if include_title and self.conversation_title and self.conversation_title != "Untitled":
            parts.append(f"[TOPIC: {self.conversation_title}]")

        # User message - THE PRIMARY SIGNAL for self-effacing patterns
        if self.user_message:
            if mode == "minimal":
                return self.user_message
            parts.append(self.user_message)

        # Assistant response (shaped by AI's model of you)
        if self.assistant_message and mode in ["balanced", "full"]:
            assistant = self.assistant_message

            # Truncate long responses (keeps first and last portions)
            if mode == "balanced" and len(assistant) > max_assistant_chars:
                half = max_assistant_chars // 2
                assistant = assistant[:half] + "\n[...]\n" + assistant[-half:]

            parts.append(f"[RESPONSE] {assistant}")

        # AI interpretations (static for ChatGPT, but useful for cross-platform comparison)
        if include_interpretations and self.ai_interpretations:

            # Platform-specific interpretation extraction
            if self.platform == "chatgpt":
                user_context = self.ai_interpretations.get('user_context_message_data', {})
                about_user = user_context.get('about_user_message', '')
                about_model = user_context.get('about_model_message', '')

                if about_user:
                    parts.append(f"[AI_UNDERSTANDING] {about_user}")
                if about_model:
                    parts.append(f"[AI_NOTES] {about_model}")

            elif self.platform == "claude":
                # Claude interpretation format (TBD)
                if self.ai_interpretations.get('thinking'):
                    parts.append(f"[AI_THINKING] {self.ai_interpretations['thinking']}")
                if self.ai_interpretations.get('user_model'):
                    parts.append(f"[AI_UNDERSTANDING] {self.ai_interpretations['user_model']}")

        # System context (hidden prompts, system messages)
        if include_interpretations and self.system_context:
            system_notes = []
            for key, value in self.system_context.items():
                if value and isinstance(value, (str, list)):
                    if isinstance(value, list):
                        value = ', '.join(str(v) for v in value)
                    system_notes.append(f"{key}: {value}")
            if system_notes:
                parts.append(f"[SYSTEM] {' | '.join(system_notes)}")

        # Tool usage (web searches, function calls)
        if self.tool_usage and mode == "full":
            tool_summary = []
            for tool in self.tool_usage:
                if 'search_result_groups' in tool:
                    domains = [g.get('domain', '') for g in tool['search_result_groups']]
                    tool_summary.append(f"searched: {', '.join(domains)}")
                elif 'tool_name' in tool:
                    tool_summary.append(f"used: {tool['tool_name']}")
            if tool_summary:
                parts.append(f"[TOOLS] {' | '.join(tool_summary)}")

        return '\n\n'.join(parts)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with datetime serialization"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UniversalChunk':
        """Create from dictionary"""
        # Handle datetime parsing
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if isinstance(data.get('conversation_start'), str):
            data['conversation_start'] = datetime.fromisoformat(data['conversation_start'])
        
        return cls(**data)

class ConversationCollection:
    """
    Collection of conversation chunks with cross-platform analysis capabilities
    """
    
    def __init__(self, chunks: List[UniversalChunk] = None):
        self.chunks = chunks or []
    
    def add_chunk(self, chunk: UniversalChunk):
        """Add a chunk to the collection"""
        self.chunks.append(chunk)
    
    def get_platforms(self) -> List[str]:
        """Get unique platforms in the collection"""
        return list(set(chunk.platform for chunk in self.chunks))
    
    def get_date_range(self) -> tuple:
        """Get earliest and latest conversation dates"""
        if not self.chunks:
            return None, None
        
        dates = [chunk.timestamp for chunk in self.chunks if chunk.timestamp]
        return min(dates), max(dates)
    
    def get_platform_stats(self) -> Dict[str, Dict]:
        """Get statistics by platform"""
        stats = {}
        
        for platform in self.get_platforms():
            platform_chunks = [c for c in self.chunks if c.platform == platform]
            
            stats[platform] = {
                'chunk_count': len(platform_chunks),
                'conversation_count': len(set(c.conversation_id for c in platform_chunks)),
                'date_range': self._get_platform_date_range(platform_chunks),
                'has_interpretations': sum(1 for c in platform_chunks if c.ai_interpretations),
                'has_tool_usage': sum(1 for c in platform_chunks if c.tool_usage)
            }
        
        return stats
    
    def _get_platform_date_range(self, chunks: List[UniversalChunk]) -> tuple:
        """Get date range for specific chunks"""
        dates = [c.timestamp for c in chunks if c.timestamp]
        if not dates:
            return None, None
        return min(dates), max(dates)
    
    def save_to_json(self, filepath: str, compact: bool = True, deduplicate_interpretations: bool = True):
        """
        Save collection to JSON file with optimizations

        Args:
            filepath: Output path
            compact: Use compact JSON (no indentation) - reduces file size by ~40%
            deduplicate_interpretations: Store unique interpretations separately and reference by ID
        """

        if deduplicate_interpretations:
            # Build interpretation lookup table
            interpretation_map = {}
            interpretation_id = 0

            for chunk in self.chunks:
                if chunk.ai_interpretations:
                    # Create hashable key from interpretation
                    interp_key = json.dumps(chunk.ai_interpretations, sort_keys=True, default=str)

                    if interp_key not in interpretation_map:
                        interpretation_map[interp_key] = f"interp_{interpretation_id}"
                        interpretation_id += 1

            # Create reverse lookup
            interpretations_store = {
                v: json.loads(k) for k, v in interpretation_map.items()
            }

            # Build chunks with interpretation references
            optimized_chunks = []
            for chunk in self.chunks:
                chunk_dict = chunk.to_dict()

                if chunk.ai_interpretations:
                    interp_key = json.dumps(chunk.ai_interpretations, sort_keys=True, default=str)
                    chunk_dict['ai_interpretation_ref'] = interpretation_map[interp_key]
                    chunk_dict['ai_interpretations'] = None  # Remove duplicate data

                optimized_chunks.append(chunk_dict)

            data = {
                'chunks': optimized_chunks,
                'interpretations': interpretations_store,
                'metadata': {
                    'total_chunks': len(self.chunks),
                    'platforms': self.get_platforms(),
                    'date_range': self.get_date_range(),
                    'created_at': datetime.now().isoformat(),
                    'unique_interpretations': len(interpretations_store),
                    'deduplication_savings': f"{(1 - len(interpretations_store)/len([c for c in self.chunks if c.ai_interpretations]))*100:.1f}%" if any(c.ai_interpretations for c in self.chunks) else "N/A"
                }
            }
        else:
            data = {
                'chunks': [chunk.to_dict() for chunk in self.chunks],
                'metadata': {
                    'total_chunks': len(self.chunks),
                    'platforms': self.get_platforms(),
                    'date_range': self.get_date_range(),
                    'created_at': datetime.now().isoformat()
                }
            }

        with open(filepath, 'w') as f:
            if compact:
                json.dump(data, f, default=str, separators=(',', ':'))
            else:
                json.dump(data, f, default=str, indent=2)
    
    @classmethod
    def load_from_json(cls, filepath: str) -> 'ConversationCollection':
        """Load collection from JSON file (handles both optimized and legacy formats)"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Check if this is the optimized format with deduplicated interpretations
        interpretations_store = data.get('interpretations', {})

        chunks = []
        for chunk_data in data['chunks']:
            # Restore interpretations from reference if present
            if 'ai_interpretation_ref' in chunk_data:
                interp_ref = chunk_data['ai_interpretation_ref']
                chunk_data['ai_interpretations'] = interpretations_store.get(interp_ref, {})
                del chunk_data['ai_interpretation_ref']

            chunks.append(UniversalChunk.from_dict(chunk_data))

        return cls(chunks)

# Utility functions for cross-platform analysis
def compare_ai_interpretations(chunks: List[UniversalChunk], user_pattern: str) -> Dict:
    """
    Compare how different AIs interpreted the same user pattern
    
    This is where the magic happens - seeing how ChatGPT vs Claude
    understood your communication style differently.
    """
    results = {}
    
    for platform in set(chunk.platform for chunk in chunks):
        platform_chunks = [c for c in chunks if c.platform == platform]
        interpretations = []
        
        for chunk in platform_chunks:
            if user_pattern.lower() in chunk.user_message.lower():
                if chunk.ai_interpretations:
                    interpretations.append(chunk.ai_interpretations)
        
        results[platform] = {
            'interpretation_count': len(interpretations),
            'interpretations': interpretations
        }
    
    return results

def find_cross_platform_evolution(chunks: List[UniversalChunk], topic: str) -> List[UniversalChunk]:
    """
    Find how thinking on a topic evolved across platforms and time
    """
    relevant_chunks = []
    
    for chunk in chunks:
        if topic.lower() in (chunk.user_message or "").lower():
            relevant_chunks.append(chunk)
    
    # Sort by timestamp to see evolution
    return sorted(relevant_chunks, key=lambda x: x.timestamp or datetime.min)
