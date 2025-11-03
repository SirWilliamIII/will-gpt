"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class SearchMode(str, Enum):
    """Available search modes"""
    VECTOR = "vector"  # Standard vector similarity search
    RECOMMEND = "recommend"  # Find similar with positive/negative examples
    DISCOVER = "discover"  # Search with context constraints
    ORDER_BY = "order_by"  # Sort by field instead of relevance
    MMR = "mmr"  # Maximal Marginal Relevance (diverse results)
    GROUPS = "groups"  # Group results by field


class SearchFilters(BaseModel):
    """Search filter parameters"""
    platform: Optional[str] = Field(None, description="Filter by platform (chatgpt, claude, claude-projects)")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return")
    with_interpretations: bool = Field(False, description="Only return results with AI interpretations")
    date_from: Optional[str] = Field(None, description="Filter by date (ISO format)")
    date_to: Optional[str] = Field(None, description="Filter by date (ISO format)")
    metadata_filter: Optional[str] = Field(None, description="Metadata filter in format 'key:value'")

    # Search mode parameters
    search_mode: SearchMode = Field(SearchMode.VECTOR, description="Search mode to use")

    # Recommend mode parameters
    positive_ids: Optional[List[str]] = Field(None, description="Positive example point IDs for recommend mode")
    negative_ids: Optional[List[str]] = Field(None, description="Negative example point IDs for recommend mode")

    # Order by parameters
    order_by_field: Optional[str] = Field(None, description="Field to order results by (e.g., 'timestamp')")
    order_direction: Literal["asc", "desc"] = Field("desc", description="Sort direction")

    # MMR parameters
    mmr_diversity: Optional[float] = Field(None, ge=0, le=1, description="MMR diversity lambda (0=relevance, 1=diversity)")

    # Groups parameters
    group_by: Optional[str] = Field(None, description="Field to group results by (e.g., 'platform', 'conversation_id')")
    group_size: Optional[int] = Field(3, ge=1, le=10, description="Number of results per group")


class SearchResult(BaseModel):
    """Single search result"""
    id: int = Field(..., description="Result ID")
    score: float = Field(..., description="Relevance score (0-1)")
    platform: str = Field(..., description="Platform (chatgpt, claude, claude-projects)")
    conversation_title: str = Field(..., description="Conversation title")
    timestamp: Optional[str] = Field(None, description="Message timestamp (ISO format)")
    turn_number: int = Field(..., description="Turn number in conversation")

    user_message: str = Field(..., description="User's message")
    assistant_message: str = Field(..., description="Assistant's response")

    has_interpretations: bool = Field(False, description="Whether AI interpretations are present")
    about_user: Optional[str] = Field(None, description="AI's interpretation about user")
    about_model: Optional[str] = Field(None, description="AI's interpretation about model")

    user_message_type: Optional[str] = Field(None, description="Type of user message")
    assistant_message_type: Optional[str] = Field(None, description="Type of assistant message")
    assistant_model: Optional[str] = Field(None, description="Model used for response")


class SearchResponse(BaseModel):
    """Search API response"""
    query: str = Field(..., description="Search query")
    total_results: int = Field(..., description="Number of results returned")
    execution_time_ms: float = Field(..., description="Search execution time in milliseconds")
    results: List[SearchResult] = Field(..., description="Search results")
    filters: SearchFilters = Field(..., description="Applied filters")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether BGE-M3 model is loaded")
    qdrant_connected: bool = Field(..., description="Whether Qdrant is accessible")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class GroupedResults(BaseModel):
    """Results grouped by a field"""
    group_key: str = Field(..., description="The group identifier (e.g., platform name)")
    hits: List[SearchResult] = Field(..., description="Search results in this group")


class GroupedSearchResponse(BaseModel):
    """Search API response with grouped results"""
    query: str = Field(..., description="Search query")
    total_groups: int = Field(..., description="Number of groups returned")
    execution_time_ms: float = Field(..., description="Search execution time in milliseconds")
    groups: List[GroupedResults] = Field(..., description="Grouped search results")
    filters: SearchFilters = Field(..., description="Applied filters")


class BatchSearchRequest(BaseModel):
    """Request for batch search"""
    queries: List[str] = Field(..., description="List of search queries", min_length=1, max_length=10)
    filters: SearchFilters = Field(default_factory=SearchFilters, description="Filters to apply to all searches")


class BatchSearchResponse(BaseModel):
    """Batch search API response"""
    results: List[SearchResponse] = Field(..., description="Results for each query")
    total_execution_time_ms: float = Field(..., description="Total execution time in milliseconds")
