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

class ChessQLRequest(BaseModel):
    """Request model for ChessQL queries."""
    query: str
    limit: Optional[int] = 100

class NaturalLanguageRequest(BaseModel):
    """Request model for natural language queries."""
    question: str
    limit: Optional[int] = 100

class QueryResponse(BaseModel):
    """Response model for query results."""
    success: bool
    results: List[Dict[str, Any]]
    count: int
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
            "/query": "Execute natural language queries",
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
    """
    try:
        if query_lang is None:
            raise HTTPException(status_code=500, detail="Query language not initialized")
        
        # Execute the query
        results = query_lang.execute_query(request.query)
        
        # Apply limit
        if request.limit and request.limit > 0:
            results = results[:request.limit]
        
        return QueryResponse(
            success=True,
            results=results,
            count=len(results),
            query=request.query
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            results=[],
            count=0,
            query=request.query,
            error=str(e)
        )

@app.post("/query", response_model=QueryResponse)
async def execute_natural_language_query(request: NaturalLanguageRequest):
    """
    Execute a natural language query.
    
    Examples:
    - "Show me games where lecorvus won"
    - "Find games where queen was sacrificed"
    - "Count games where lecorvus promoted to queen x 2"
    - "Show games where lecorvus was rated over 1500"
    """
    try:
        if natural_search is None:
            raise HTTPException(status_code=500, detail="Natural language search not initialized")
        
        # Execute the natural language query
        results = natural_search.search(request.question, show_query=False)
        
        # Apply limit
        if request.limit and request.limit > 0:
            results = results[:request.limit]
        
        return QueryResponse(
            success=True,
            results=results,
            count=len(results),
            query=request.question
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            results=[],
            count=0,
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
                "description": "Get all games where lecorvus played white"
            },
            {
                "query": "SELECT COUNT(*) FROM games WHERE (lecorvus won)",
                "description": "Count games where lecorvus won"
            },
            {
                "query": "SELECT * FROM games WHERE (queen sacrificed)",
                "description": "Find games with queen sacrifices"
            },
            {
                "query": "SELECT * FROM games WHERE (pawn promoted to queen x 2)",
                "description": "Find games with two queen promotions"
            },
            {
                "query": "SELECT * FROM games WHERE (lecorvus won) AND (queen sacrificed)",
                "description": "Find games where lecorvus won and sacrificed queen"
            }
        ],
        "natural_language_examples": [
            {
                "question": "Show me games where lecorvus won",
                "description": "Get all wins by lecorvus"
            },
            {
                "question": "Find games where queen was sacrificed",
                "description": "Find games with queen sacrifices"
            },
            {
                "question": "Count games where lecorvus promoted to queen x 2",
                "description": "Count games with two queen promotions by lecorvus"
            },
            {
                "question": "Show games where lecorvus was rated over 1500",
                "description": "Find games where lecorvus had high rating"
            },
            {
                "question": "Find games where lecorvus won and sacrificed queen",
                "description": "Find wins where lecorvus sacrificed queen"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
