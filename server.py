"""
FastAPI Server for ChessQL
Provides REST API endpoints for chess game queries.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import time
from query_language import ChessQueryLanguage
from natural_language_search import NaturalLanguageSearch
from accounts import AccountManager
from lichess_auth import LichessAuth, LichessAuthError, verify_token, revoke_token, add_token_manually
from lichess_sync import get_sync_manager, LichessGame, SyncStatus, LichessSyncError
from database import ChessDatabase

app = FastAPI(
    title="ChessQL API",
    description="REST API for chess game database queries",
    version="1.0.0"
)

# Add CORS middleware for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances - will be initialized on startup
query_lang = None
natural_search = None
account_manager = None
lichess_auth = None
chess_db = None

# Background sync tasks
_sync_tasks: Dict[str, Any] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the query processors on startup."""
    global query_lang, natural_search, account_manager, lichess_auth, chess_db
    
    db_path = os.getenv("CHESSQL_DB_PATH", "chess_games.db")
    reference_player = os.getenv("CHESSQL_REFERENCE_PLAYER", "lecorvus")
    
    # Lichess OAuth2 configuration
    lichess_client_id = os.getenv("LICHESS_CLIENT_ID", "chessql-desktop")
    lichess_redirect_uri = os.getenv("LICHESS_REDIRECT_URI", "http://localhost:9090/auth/lichess/callback")
    
    # Initialize database
    chess_db = ChessDatabase(db_path)
    
    # Initialize account manager (creates tables if needed)
    account_manager = AccountManager(db_path)
    
    # Initialize Lichess auth handler
    lichess_auth = LichessAuth(lichess_client_id, lichess_redirect_uri)
    
    # Only initialize query processors if database exists
    if os.path.exists(db_path):
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
        "natural_search_ready": natural_search is not None,
        "auth_ready": lichess_auth is not None
    }


# ============================================================================
# Authentication Endpoints
# ============================================================================

class AuthStartResponse(BaseModel):
    """Response for starting OAuth flow."""
    auth_url: str
    state: str
    code_verifier: str  # Required for desktop apps to complete PKCE flow


class AuthCallbackRequest(BaseModel):
    """Request for completing OAuth flow."""
    code: str
    state: str
    code_verifier: Optional[str] = None  # Required for desktop apps that manage PKCE client-side


class AuthCallbackResponse(BaseModel):
    """Response for completed OAuth flow."""
    success: bool
    username: Optional[str] = None
    error: Optional[str] = None


class AccountResponse(BaseModel):
    """Response model for account info."""
    id: int
    username: str
    token_expires_at: Optional[int] = None
    created_at: str
    last_sync_at: Optional[str] = None
    last_game_at: Optional[int] = None
    games_count: int


@app.post("/auth/lichess/start", response_model=AuthStartResponse)
async def start_lichess_auth():
    """
    Start the Lichess OAuth2 authorization flow.
    
    Returns an authorization URL that the user should open in their browser.
    The 'state' and 'code_verifier' parameters should be saved for the callback.
    For desktop apps, the code_verifier is needed to complete the PKCE flow.
    """
    if lichess_auth is None:
        raise HTTPException(status_code=500, detail="Lichess auth not initialized")
    
    auth_url, state, code_verifier = lichess_auth.start_authorization()
    
    return AuthStartResponse(auth_url=auth_url, state=state, code_verifier=code_verifier)


@app.post("/auth/lichess/callback", response_model=AuthCallbackResponse)
async def complete_lichess_auth(request: AuthCallbackRequest):
    """
    Complete the Lichess OAuth2 authorization flow.
    
    Exchange the authorization code for an access token and save the account.
    For desktop apps, pass the code_verifier that was returned from /auth/lichess/start.
    """
    if lichess_auth is None:
        raise HTTPException(status_code=500, detail="Lichess auth not initialized")
    
    if account_manager is None:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    try:
        result = await lichess_auth.complete_authorization(
            request.code, 
            request.state, 
            code_verifier=request.code_verifier
        )
        
        # Calculate token expiration timestamp
        expires_at = None
        if result.expires_in:
            expires_at = int(time.time()) + result.expires_in
        
        # Save the account
        account_manager.add_account(
            username=result.username,
            access_token=result.access_token,
            token_expires_at=expires_at
        )
        
        return AuthCallbackResponse(success=True, username=result.username)
        
    except LichessAuthError as e:
        return AuthCallbackResponse(success=False, error=str(e))


@app.get("/auth/lichess/callback")
async def lichess_oauth_callback(code: str, state: str):
    """
    OAuth2 callback endpoint for browser redirect.
    
    This endpoint is called by Lichess after the user authorizes the app.
    It completes the OAuth flow and returns an HTML page with the result.
    """
    if lichess_auth is None:
        return {"error": "Lichess auth not initialized"}
    
    if account_manager is None:
        return {"error": "Account manager not initialized"}
    
    try:
        result = await lichess_auth.complete_authorization(code, state)
        
        # Calculate token expiration timestamp
        expires_at = None
        if result.expires_in:
            expires_at = int(time.time()) + result.expires_in
        
        # Save the account
        account_manager.add_account(
            username=result.username,
            access_token=result.access_token,
            token_expires_at=expires_at
        )
        
        # Return a simple HTML page that can close itself or redirect
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ChessQL - Authorization Complete</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: #fff;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 16px;
                    backdrop-filter: blur(10px);
                }}
                h1 {{ color: #4ade80; margin-bottom: 10px; }}
                p {{ color: #94a3b8; }}
                .username {{ color: #60a5fa; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✓ Authorization Successful!</h1>
                <p>Logged in as <span class="username">{result.username}</span></p>
                <p>You can close this window and return to ChessQL.</p>
            </div>
            <script>
                // Notify opener if exists
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'lichess-auth-success',
                        username: '{result.username}'
                    }}, '*');
                }}
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
        
    except LichessAuthError as e:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ChessQL - Authorization Failed</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: #fff;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 16px;
                    backdrop-filter: blur(10px);
                }}
                h1 {{ color: #f87171; margin-bottom: 10px; }}
                p {{ color: #94a3b8; }}
                .error {{ color: #fbbf24; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✗ Authorization Failed</h1>
                <p class="error">{str(e)}</p>
                <p>Please close this window and try again.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=400)


class ManualTokenRequest(BaseModel):
    """Request for adding a manually created token."""
    access_token: str


@app.post("/auth/lichess/token", response_model=AuthCallbackResponse)
async def add_manual_token(request: ManualTokenRequest):
    """
    Add a manually created Lichess personal access token.
    
    Users can create tokens at: https://lichess.org/account/oauth/token
    Required scope: preference:read (minimum)
    """
    if account_manager is None:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    # Verify the token and get account info
    account_info = await add_token_manually(request.access_token)
    
    if not account_info:
        return AuthCallbackResponse(
            success=False, 
            error="Invalid token. Please check the token and try again."
        )
    
    username = account_info.get('username')
    
    # Save the account (personal tokens don't expire)
    account_manager.add_account(
        username=username,
        access_token=request.access_token,
        token_expires_at=None  # Personal tokens don't expire
    )
    
    return AuthCallbackResponse(success=True, username=username)


@app.get("/auth/accounts", response_model=List[AccountResponse])
async def list_accounts():
    """
    List all linked Lichess accounts.
    
    Note: Access tokens are not included in the response for security.
    """
    if account_manager is None:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    accounts = account_manager.list_accounts()
    return accounts


@app.delete("/auth/accounts/{username}")
async def remove_account(username: str):
    """
    Remove a linked Lichess account.
    
    This will also revoke the access token on Lichess.
    """
    if account_manager is None:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    # Get the account to retrieve the token for revocation
    account = account_manager.get_account(username)
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{username}' not found")
    
    # Try to revoke the token on Lichess (best effort)
    if account.get('access_token'):
        await revoke_token(account['access_token'])
    
    # Remove from local database
    removed = account_manager.remove_account(username)
    
    if removed:
        return {"success": True, "message": f"Account '{username}' removed"}
    else:
        raise HTTPException(status_code=404, detail=f"Account '{username}' not found")


@app.get("/auth/accounts/{username}/verify")
async def verify_account(username: str):
    """
    Verify that an account's token is still valid.
    """
    if account_manager is None:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    account = account_manager.get_account(username)
    
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{username}' not found")
    
    # Verify token with Lichess
    account_info = await verify_token(account['access_token'])
    
    if account_info:
        return {
            "valid": True,
            "username": account_info.get('username'),
            "title": account_info.get('title'),
            "patron": account_info.get('patron', False)
        }
    else:
        return {"valid": False, "message": "Token is invalid or expired"}


# ============================================================================
# Game Sync Endpoints
# ============================================================================

class SyncStartRequest(BaseModel):
    """Request for starting a sync operation."""
    max_games: Optional[int] = None  # Limit for testing


class SyncProgressResponse(BaseModel):
    """Response for sync progress."""
    status: str
    total_games: Optional[int] = None
    synced_games: int = 0
    new_games: int = 0
    skipped_games: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


async def _run_sync_task(username: str, access_token: str, account_id: int, since: Optional[int], max_games: Optional[int]):
    """Background task to sync games."""
    import asyncio
    from datetime import datetime
    from piece_analysis import ChessPieceAnalyzer
    
    sync_manager = get_sync_manager()
    progress = sync_manager.get_progress(username.lower())
    
    # Initialize piece analyzer for capture analysis
    piece_analyzer = ChessPieceAnalyzer(reference_player=username)
    
    new_games_count = 0
    skipped_count = 0
    latest_game_ts = since
    
    try:
        async for game in sync_manager.stream_games(
            username=username,
            access_token=access_token,
            since=since,
            max_games=max_games,
            with_opening=True,
        ):
            # Check for cancellation
            if sync_manager._cancel_flags.get(username.lower(), False):
                progress.status = SyncStatus.CANCELLED
                break
            
            # Convert to database format
            game_data = game.to_pgn_dict()
            
            # Check if game already exists
            if chess_db.game_exists(game.id):
                skipped_count += 1
                progress.skipped_games = skipped_count
            else:
                # Insert game
                try:
                    game_id = chess_db.insert_game(game_data, account_id=account_id)
                    
                    # Analyze captures
                    if game.moves:
                        captures = piece_analyzer.analyze_captures(
                            game.moves,
                            game.white_player,
                            game.black_player,
                            username
                        )
                        if captures:
                            chess_db.insert_captures(game_id, captures)
                    
                    new_games_count += 1
                    progress.new_games = new_games_count
                except Exception as e:
                    # Skip games that fail to insert (e.g., duplicates)
                    skipped_count += 1
                    progress.skipped_games = skipped_count
            
            progress.synced_games += 1
            
            # Track latest game timestamp for incremental sync
            if game.created_at and (latest_game_ts is None or game.created_at > latest_game_ts):
                latest_game_ts = game.created_at
        
        if progress.status != SyncStatus.CANCELLED:
            progress.status = SyncStatus.COMPLETED
        
        # Update account sync status
        if account_manager and latest_game_ts:
            account_manager.update_sync_status(
                username=username,
                last_sync_at=datetime.now(),
                last_game_at=latest_game_ts,
                games_count=chess_db.get_games_count_by_account(account_id)
            )
        
    except LichessSyncError as e:
        progress.status = SyncStatus.ERROR
        progress.error_message = str(e)
    except Exception as e:
        progress.status = SyncStatus.ERROR
        progress.error_message = f"Unexpected error: {str(e)}"
    
    progress.completed_at = datetime.now()
    
    # Clean up task reference
    if username.lower() in _sync_tasks:
        del _sync_tasks[username.lower()]


@app.post("/sync/start/{username}", response_model=SyncProgressResponse)
async def start_sync(username: str, request: SyncStartRequest = None):
    """
    Start syncing games for an account from Lichess.
    
    This initiates a background sync that downloads all games for the account.
    Use GET /sync/status/{username} to check progress.
    
    For incremental sync, the system automatically uses the last sync timestamp.
    """
    import asyncio
    
    if account_manager is None or chess_db is None:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    # Get account
    account = account_manager.get_account(username)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{username}' not found")
    
    # Check if sync already in progress
    sync_manager = get_sync_manager()
    if sync_manager.is_syncing(username.lower()):
        raise HTTPException(status_code=409, detail="Sync already in progress")
    
    # Get last sync timestamp for incremental sync
    since = account.get('last_game_at')
    if since:
        since = since + 1  # Start from the next millisecond
    
    # Initialize progress
    from datetime import datetime
    progress = sync_manager._sync_progress[username.lower()] = sync_manager.get_progress(username.lower())
    progress.status = SyncStatus.SYNCING
    progress.started_at = datetime.now()
    progress.synced_games = 0
    progress.new_games = 0
    progress.skipped_games = 0
    progress.error_message = None
    progress.completed_at = None
    sync_manager._cancel_flags[username.lower()] = False
    
    # Start background task
    max_games = request.max_games if request else None
    task = asyncio.create_task(_run_sync_task(
        username=username,
        access_token=account['access_token'],
        account_id=account['id'],
        since=since,
        max_games=max_games
    ))
    _sync_tasks[username.lower()] = task
    
    return SyncProgressResponse(
        status=progress.status.value,
        synced_games=0,
        new_games=0,
        skipped_games=0,
        started_at=progress.started_at.isoformat() if progress.started_at else None
    )


@app.get("/sync/status/{username}", response_model=SyncProgressResponse)
async def get_sync_status(username: str):
    """
    Get the current sync progress for an account.
    """
    sync_manager = get_sync_manager()
    progress = sync_manager.get_progress(username.lower())
    
    return SyncProgressResponse(
        status=progress.status.value,
        total_games=progress.total_games,
        synced_games=progress.synced_games,
        new_games=progress.new_games,
        skipped_games=progress.skipped_games,
        error_message=progress.error_message,
        started_at=progress.started_at.isoformat() if progress.started_at else None,
        completed_at=progress.completed_at.isoformat() if progress.completed_at else None
    )


@app.post("/sync/stop/{username}")
async def stop_sync(username: str):
    """
    Cancel an ongoing sync operation.
    """
    sync_manager = get_sync_manager()
    
    if not sync_manager.is_syncing(username.lower()):
        raise HTTPException(status_code=404, detail="No sync in progress")
    
    sync_manager.cancel_sync(username.lower())
    
    return {"success": True, "message": f"Sync cancellation requested for '{username}'"}


@app.get("/sync/games/{username}")
async def get_synced_games_count(username: str):
    """
    Get the count of synced games for an account.
    """
    if account_manager is None or chess_db is None:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    account = account_manager.get_account(username)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{username}' not found")
    
    count = chess_db.get_games_count_by_account(account['id'])
    
    return {
        "username": username,
        "games_count": count,
        "last_sync_at": account.get('last_sync_at'),
        "last_game_at": account.get('last_game_at')
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
