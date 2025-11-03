"""
FastAPI application for WillGPT search interface

Main entry point for the web API
"""

import os
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from pathlib import Path

from api.models import (
    SearchResponse, SearchFilters, HealthResponse, ErrorResponse,
    SearchMode, GroupedSearchResponse, BatchSearchRequest, BatchSearchResponse
)
from api.search_service import SearchService

# Load environment variables
load_dotenv()

# Environment configuration
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')
MODEL_NAME = os.getenv('MODEL_NAME', 'BAAI/bge-m3')

# Device detection
DEVICE = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model once at startup, cleanup on shutdown"""
    # Startup: Load model
    print(f"Loading BGE-M3 model on device: {DEVICE}...")
    app.state.search_service = SearchService(
        qdrant_url=QDRANT_URL,
        qdrant_api_key=QDRANT_API_KEY,
        collection_name=COLLECTION_NAME,
        model_name=MODEL_NAME,
        device=DEVICE
    )
    app.state.search_service.load_model()
    print("Model loaded successfully")

    yield

    # Shutdown: Cleanup if needed
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="WillGPT Search API",
    description="Search your AI conversation history across ChatGPT, Claude, and Claude Projects",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Endpoints

@app.get("/", response_class=FileResponse)
async def root():
    """Serve frontend HTML"""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "WillGPT Search API", "docs": "/docs"}


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    health = app.state.search_service.health_check()
    return HealthResponse(
        status="healthy" if health["model_loaded"] and health["qdrant_connected"] else "degraded",
        model_loaded=health["model_loaded"],
        qdrant_connected=health["qdrant_connected"]
    )


@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query", min_length=1),
    platform: str = Query(None, description="Filter by platform (chatgpt, claude, claude-projects)"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    interpretations: bool = Query(False, description="Only show results with AI interpretations"),
    date_from: str = Query(None, description="Filter by date from (ISO format)"),
    date_to: str = Query(None, description="Filter by date to (ISO format)"),
    metadata_filter: str = Query(None, description="Metadata filter (key:value)"),

    # Search mode parameters
    search_mode: SearchMode = Query(SearchMode.VECTOR, description="Search mode"),
    positive_ids: str = Query(None, description="Comma-separated positive IDs for recommend mode"),
    negative_ids: str = Query(None, description="Comma-separated negative IDs for recommend mode"),
    order_by_field: str = Query(None, description="Field to order by (e.g., 'timestamp')"),
    order_direction: str = Query("desc", description="Sort direction (asc/desc)"),
    mmr_diversity: float = Query(None, ge=0, le=1, description="MMR diversity (0=relevance, 1=diversity)"),
    group_by: str = Query(None, description="Field to group by (e.g., 'platform')"),
    group_size: int = Query(3, ge=1, le=10, description="Results per group")
):
    """
    Execute search across conversation history.

    Supports multiple search modes:
    - vector: Standard hybrid vector search (dense + sparse)
    - recommend: Find similar using positive/negative examples
    - order_by: Sort by field instead of relevance
    - mmr: Maximal Marginal Relevance for diverse results
    - groups: Group results by field

    Returns relevant conversation chunks with scores and metadata.
    """
    try:
        # Parse list parameters
        positive_list = positive_ids.split(",") if positive_ids else None
        negative_list = negative_ids.split(",") if negative_ids else None

        # Build filters
        filters = SearchFilters(
            platform=platform,
            limit=limit,
            with_interpretations=interpretations,
            date_from=date_from,
            date_to=date_to,
            metadata_filter=metadata_filter,
            search_mode=search_mode,
            positive_ids=positive_list,
            negative_ids=negative_list,
            order_by_field=order_by_field,
            order_direction=order_direction,
            mmr_diversity=mmr_diversity,
            group_by=group_by,
            group_size=group_size
        )

        # Execute search
        results, execution_time_ms = app.state.search_service.search(q, filters)

        # Return appropriate response based on search mode
        if search_mode == SearchMode.GROUPS:
            return GroupedSearchResponse(
                query=q,
                total_groups=len(results),
                execution_time_ms=round(execution_time_ms, 2),
                groups=results,
                filters=filters
            )
        else:
            return SearchResponse(
                query=q,
                total_results=len(results),
                execution_time_ms=round(execution_time_ms, 2),
                results=results,
                filters=filters
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Mount static files for frontend assets
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
