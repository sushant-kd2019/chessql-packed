"""
FastAPI Server for ChessQL
Provides REST API endpoints for chess game queries.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from query_language import ChessQueryLanguage
from natural_language_search import NaturalLanguageSearch

app = FastAPI(
    title="ChessQL API",
    description="REST API for chess game database queries",
    version="1.0.0"
)

# Global instances - will be initialized on startup
query_lang = None
natural_search = None

@app.on_event("startup")
async def startup_event():
    """Initialize the query processors on startup."""
    global query_lang, natural_search
    
    db_path = os.getenv("CHESSQL_DB_PATH", "chess_games.db")
    reference_player = os.getenv("CHESSQL_REFERENCE_PLAYER", "lecorvus")
    
    if not os.path.exists(db_path):
        raise HTTPException(
            status_code=500, 
            detail=f"Database file '{db_path}' not found. Please run ingestion first."
        )
    
    query_lang = ChessQueryLanguage(db_path, reference_player)
    natural_search = NaturalLanguageSearch(db_path, reference_player=reference_player)

def calculate_pagination(page_no: int, limit: int, offset: Optional[int] = None, total_count: Optional[int] = None):
    """Calculate pagination parameters."""
    # If offset is provided, use it directly; otherwise calculate from page_no
    if offset is not None:
        actual_offset = offset
        actual_page_no = (offset // limit) + 1
    else:
        actual_offset = (page_no - 1) * limit
        actual_page_no = page_no
    
    # Calculate pagination metadata
    pagination_info = {
        "page_no": actual_page_no,
        "limit": limit,
        "offset": actual_offset,
        "total_pages": None,
        "has_next": None,
        "has_prev": None
    }
    
    if total_count is not None:
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        pagination_info.update({
            "total_pages": total_pages,
            "has_next": actual_page_no < total_pages,
            "has_prev": actual_page_no > 1
        })
    
    return pagination_info

class ChessQLRequest(BaseModel):
    """Request model for ChessQL queries."""
    query: str
    limit: Optional[int] = 100
    page_no: Optional[int] = 1
    offset: Optional[int] = None

class NaturalLanguageRequest(BaseModel):
    """Request model for natural language queries."""
    question: str
    limit: Optional[int] = 100
    page_no: Optional[int] = 1
    offset: Optional[int] = None

class QueryResponse(BaseModel):
    """Response model for query results."""
    success: bool
    results: List[Dict[str, Any]]
    count: int
    total_count: Optional[int] = None
    page_no: int
    limit: int
    offset: int
    total_pages: Optional[int] = None
    has_next: Optional[bool] = None
    has_prev: Optional[bool] = None
    query: Optional[str] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "ChessQL API",
        "version": "1.0.0",
        "endpoints": {
            "/cql": "Execute ChessQL queries (SQL + chess patterns)",
            "/ask": "Execute natural language queries",
            "/docs": "API documentation",
            "/health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database_exists": os.path.exists(os.getenv("CHESSQL_DB_PATH", "chess_games.db")),
        "query_lang_ready": query_lang is not None,
        "natural_search_ready": natural_search is not None
    }

@app.post("/cql", response_model=QueryResponse)
async def execute_chessql_query(request: ChessQLRequest):
    """
    Execute a ChessQL query.
    
    Supports:
    - SQL queries: SELECT * FROM games WHERE white_player = 'lecorvus'
    - Chess patterns: (lecorvus won), (queen sacrificed), (pawn promoted to queen x 2)
    - Combined queries: (lecorvus won) AND (queen sacrificed)
    
    Pagination:
    - page_no: Page number (1-based, default: 1)
    - limit: Results per page (default: 100)
    - offset: Direct offset (overrides page_no if provided)
    """
    try:
        if query_lang is None:
            raise HTTPException(status_code=500, detail="Query language not initialized")
        
        # Execute the query
        results = query_lang.execute_query(request.query)
        total_count = len(results)
        
        # Calculate pagination
        pagination = calculate_pagination(
            page_no=request.page_no,
            limit=request.limit,
            offset=request.offset,
            total_count=total_count
        )
        
        # Apply pagination
        start_idx = pagination["offset"]
        end_idx = start_idx + pagination["limit"]
        paginated_results = results[start_idx:end_idx]
        
        return QueryResponse(
            success=True,
            results=paginated_results,
            count=len(paginated_results),
            total_count=total_count,
            page_no=pagination["page_no"],
            limit=pagination["limit"],
            offset=pagination["offset"],
            total_pages=pagination["total_pages"],
            has_next=pagination["has_next"],
            has_prev=pagination["has_prev"],
            query=request.query
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            results=[],
            count=0,
            total_count=0,
            page_no=request.page_no,
            limit=request.limit,
            offset=request.offset or ((request.page_no - 1) * request.limit),
            total_pages=0,
            has_next=False,
            has_prev=False,
            query=request.query,
            error=str(e)
        )

@app.post("/ask", response_model=QueryResponse)
async def execute_natural_language_query(request: NaturalLanguageRequest):
    """
    Execute a natural language query.
    
    Examples:
    - "Show me games where lecorvus won"
    - "Find games where queen was sacrificed"
    - "Count games where lecorvus promoted to queen x 2"
    - "Show games where lecorvus was rated over 1500"
    
    Pagination:
    - page_no: Page number (1-based, default: 1)
    - limit: Results per page (default: 100)
    - offset: Direct offset (overrides page_no if provided)
    """
    try:
        if natural_search is None:
            raise HTTPException(status_code=500, detail="Natural language search not initialized")
        
        # Execute the natural language query
        results = natural_search.search(request.question, show_query=True)
        total_count = len(results)
        
        # Calculate pagination
        pagination = calculate_pagination(
            page_no=request.page_no,
            limit=request.limit,
            offset=request.offset,
            total_count=total_count
        )
        
        # Apply pagination
        start_idx = pagination["offset"]
        end_idx = start_idx + pagination["limit"]
        paginated_results = results[start_idx:end_idx]
        
        return QueryResponse(
            success=True,
            results=paginated_results,
            count=len(paginated_results),
            total_count=total_count,
            page_no=pagination["page_no"],
            limit=pagination["limit"],
            offset=pagination["offset"],
            total_pages=pagination["total_pages"],
            has_next=pagination["has_next"],
            has_prev=pagination["has_prev"],
            query=request.question
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            results=[],
            count=0,
            total_count=0,
            page_no=request.page_no,
            limit=request.limit,
            offset=request.offset or ((request.page_no - 1) * request.limit),
            total_pages=0,
            has_next=False,
            has_prev=False,
            query=request.question,
            error=str(e)
        )

@app.get("/examples")
async def get_examples():
    """Get example queries for both endpoints."""
    return {
        "chessql_examples": [
            {
                "query": "SELECT * FROM games WHERE white_player = 'lecorvus'",
                "description": "Get all games where lecorvus played white",
                "pagination": {
                    "page_no": 1,
                    "limit": 10,
                    "offset": 0
                }
            },
            {
                "query": "SELECT COUNT(*) FROM games WHERE (lecorvus won)",
                "description": "Count games where lecorvus won",
                "pagination": {
                    "page_no": 1,
                    "limit": 100
                }
            },
            {
                "query": "SELECT * FROM games WHERE (queen sacrificed)",
                "description": "Find games with queen sacrifices",
                "pagination": {
                    "page_no": 2,
                    "limit": 5
                }
            },
            {
                "query": "SELECT * FROM games WHERE (pawn promoted to queen x 2)",
                "description": "Find games with two queen promotions",
                "pagination": {
                    "offset": 10,
                    "limit": 3
                }
            },
            {
                "query": "SELECT * FROM games WHERE (lecorvus won) AND (queen sacrificed)",
                "description": "Find games where lecorvus won and sacrificed queen",
                "pagination": {
                    "page_no": 1,
                    "limit": 20
                }
            }
        ],
        "natural_language_examples": [
            {
                "question": "Show me games where lecorvus won",
                "description": "Get all wins by lecorvus",
                "pagination": {
                    "page_no": 1,
                    "limit": 10
                }
            },
            {
                "question": "Find games where queen was sacrificed",
                "description": "Find games with queen sacrifices",
                "pagination": {
                    "page_no": 2,
                    "limit": 5
                }
            },
            {
                "question": "Count games where lecorvus promoted to queen x 2",
                "description": "Count games with two queen promotions by lecorvus",
                "pagination": {
                    "page_no": 1,
                    "limit": 100
                }
            },
            {
                "question": "Show games where lecorvus was rated over 1500",
                "description": "Find games where lecorvus had high rating",
                "pagination": {
                    "offset": 0,
                    "limit": 3
                }
            },
            {
                "question": "Find games where lecorvus won and sacrificed queen",
                "description": "Find wins where lecorvus sacrificed queen",
                "pagination": {
                    "page_no": 1,
                    "limit": 20
                }
            }
        ],
        "pagination_parameters": {
            "page_no": "Page number (1-based, default: 1)",
            "limit": "Results per page (default: 100)",
            "offset": "Direct offset (overrides page_no if provided)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
