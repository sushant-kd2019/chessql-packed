"""
Lichess Game Sync Module
Handles streaming and syncing games from Lichess API.
"""

import asyncio
import httpx
import re
from typing import Optional, Dict, Any, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time


def calculate_speed_from_time_control(time_control: str) -> str:
    """
    Calculate speed category from time control string.
    
    Lichess formula: estimated_duration = initial_time + (40 × increment)
    
    ≤ 29s   → ultraBullet
    ≤ 179s  → bullet
    ≤ 479s  → blitz
    ≤ 1499s → rapid
    ≥ 1500s → classical
    
    Args:
        time_control: Time control string in format "initial+increment" (e.g., "300+0", "180+2")
                     Initial time is in seconds.
    
    Returns:
        Speed category: 'ultraBullet', 'bullet', 'blitz', 'rapid', or 'classical'
    """
    if not time_control:
        return ""
    
    # Parse time control string (format: "initial+increment")
    match = re.match(r'^(\d+)\+(\d+)$', time_control.strip())
    if not match:
        return ""
    
    initial_seconds = int(match.group(1))
    increment = int(match.group(2))
    estimated_duration = initial_seconds + (40 * increment)
    
    if estimated_duration <= 29:
        return "ultraBullet"
    elif estimated_duration <= 179:
        return "bullet"
    elif estimated_duration <= 479:
        return "blitz"
    elif estimated_duration <= 1499:
        return "rapid"
    else:
        return "classical"


# Lichess API configuration
LICHESS_API_BASE = "https://lichess.org/api"
LICHESS_GAMES_EXPORT_URL = f"{LICHESS_API_BASE}/games/user"

# Rate limiting: Lichess allows 15 req/sec for authenticated users
REQUEST_DELAY = 0.1  # 100ms between requests

# Only allow standard chess and Chess960 variants
# This filters out: antichess, atomic, crazyhouse, horde, kingOfTheHill, racingKings, threeCheck
ALLOWED_VARIANTS = ["standard", "chess960"]


class SyncStatus(Enum):
    """Sync operation status."""
    IDLE = "idle"
    STARTING = "starting"
    SYNCING = "syncing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class SyncProgress:
    """Progress information for a sync operation."""
    status: SyncStatus = SyncStatus.IDLE
    total_games: Optional[int] = None
    synced_games: int = 0
    new_games: int = 0
    skipped_games: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "total_games": self.total_games,
            "synced_games": self.synced_games,
            "new_games": self.new_games,
            "skipped_games": self.skipped_games,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class LichessGame:
    """Parsed Lichess game data."""
    id: str
    pgn: str
    created_at: int  # Unix timestamp in milliseconds
    last_move_at: int
    white_player: str
    black_player: str
    white_rating: Optional[int]
    black_rating: Optional[int]
    result: str
    variant: str
    speed: str
    time_control: Optional[str]
    opening_eco: Optional[str]
    opening_name: Optional[str]
    termination: str
    moves: str
    initial_fen: Optional[str] = None  # Starting FEN for Chess960 games
    
    @classmethod
    def from_ndjson(cls, data: Dict[str, Any]) -> "LichessGame":
        """Parse a Lichess NDJSON game object."""
        players = data.get("players", {})
        white = players.get("white", {})
        black = players.get("black", {})
        opening = data.get("opening", {})
        clock = data.get("clock", {})
        
        # Determine result
        winner = data.get("winner")
        if winner == "white":
            result = "1-0"
        elif winner == "black":
            result = "0-1"
        elif data.get("status") == "draw":
            result = "1/2-1/2"
        else:
            result = "*"
        
        # Build time control string
        time_control = None
        if clock:
            initial = clock.get("initial", 0)
            increment = clock.get("increment", 0)
            time_control = f"{initial}+{increment}"
        
        # Get speed from API, or calculate as fallback
        speed = data.get("speed", "")
        if not speed and time_control:
            speed = calculate_speed_from_time_control(time_control)
        
        return cls(
            id=data.get("id", ""),
            pgn=data.get("pgn", ""),
            created_at=data.get("createdAt", 0),
            last_move_at=data.get("lastMoveAt", 0),
            white_player=white.get("user", {}).get("name", "Anonymous"),
            black_player=black.get("user", {}).get("name", "Anonymous"),
            white_rating=white.get("rating"),
            black_rating=black.get("rating"),
            result=result,
            variant=data.get("variant", "standard"),
            speed=speed,
            time_control=time_control,
            opening_eco=opening.get("eco"),
            opening_name=opening.get("name"),
            termination=data.get("status", ""),
            moves=data.get("moves", ""),
            initial_fen=data.get("initialFen"),  # Chess960 starting position
        )
    
    def to_pgn_dict(self) -> Dict[str, Any]:
        """Convert to the format expected by ChessDatabase.insert_game()."""
        # Build PGN text
        date_str = datetime.fromtimestamp(self.created_at / 1000).strftime("%Y.%m.%d")
        
        pgn_lines = [
            f'[Event "Lichess {self.speed.capitalize()} Game"]',
            f'[Site "https://lichess.org/{self.id}"]',
            f'[Date "{date_str}"]',
            f'[White "{self.white_player}"]',
            f'[Black "{self.black_player}"]',
            f'[Result "{self.result}"]',
        ]
        
        if self.white_rating:
            pgn_lines.append(f'[WhiteElo "{self.white_rating}"]')
        if self.black_rating:
            pgn_lines.append(f'[BlackElo "{self.black_rating}"]')
        if self.opening_eco:
            pgn_lines.append(f'[ECO "{self.opening_eco}"]')
        if self.opening_name:
            pgn_lines.append(f'[Opening "{self.opening_name}"]')
        if self.time_control:
            pgn_lines.append(f'[TimeControl "{self.time_control}"]')
        if self.variant != "standard":
            pgn_lines.append(f'[Variant "{self.variant.capitalize()}"]')
        if self.initial_fen:
            pgn_lines.append('[SetUp "1"]')
            pgn_lines.append(f'[FEN "{self.initial_fen}"]')
        pgn_lines.append(f'[Termination "{self.termination}"]')
        
        pgn_lines.append("")
        pgn_lines.append(f"{self.moves} {self.result}")
        
        pgn_text = "\n".join(pgn_lines)
        
        return {
            "lichess_id": self.id,
            "pgn_text": pgn_text if self.pgn else pgn_text,  # Use provided PGN if available
            "moves": self.moves,
            "white_player": self.white_player,
            "black_player": self.black_player,
            "result": self.result,
            "date_played": date_str,
            "event": f"Lichess {self.speed.capitalize()} Game",
            "site": f"https://lichess.org/{self.id}",
            "round": "-",
            "eco_code": self.opening_eco or "",
            "opening": self.opening_name or "",
            "time_control": self.time_control or "",
            "white_elo": str(self.white_rating) if self.white_rating else "",
            "black_elo": str(self.black_rating) if self.black_rating else "",
            "variant": self.variant,
            "termination": self.termination,
            "created_at_ms": self.created_at,
            "speed": self.speed,  # bullet/blitz/rapid/classical/ultrabullet
        }


class LichessSyncError(Exception):
    """Custom exception for sync errors."""
    pass


class LichessSync:
    """Handles syncing games from Lichess API."""
    
    def __init__(self):
        """Initialize the sync handler."""
        # Track sync progress per username
        self._sync_progress: Dict[str, SyncProgress] = {}
        self._cancel_flags: Dict[str, bool] = {}
    
    def get_progress(self, username: str) -> SyncProgress:
        """Get sync progress for a user."""
        return self._sync_progress.get(username, SyncProgress())
    
    def cancel_sync(self, username: str) -> bool:
        """Request cancellation of a sync operation."""
        if username in self._sync_progress:
            self._cancel_flags[username] = True
            return True
        return False
    
    def is_syncing(self, username: str) -> bool:
        """Check if a sync is in progress for a user."""
        progress = self._sync_progress.get(username)
        return progress is not None and progress.status == SyncStatus.SYNCING
    
    async def stream_games(
        self,
        username: str,
        access_token: str,
        since: Optional[int] = None,
        until: Optional[int] = None,
        max_games: Optional[int] = None,
        with_pgn: bool = False,
        with_opening: bool = True,
    ) -> AsyncGenerator[LichessGame, None]:
        """
        Stream games from Lichess API.
        
        Args:
            username: Lichess username
            access_token: OAuth2 access token
            since: Unix timestamp (milliseconds) to fetch games from
            until: Unix timestamp (milliseconds) to fetch games until
            max_games: Maximum number of games to fetch
            with_pgn: Include full PGN text (increases response size)
            with_opening: Include opening information
        
        Yields:
            LichessGame objects
        """
        url = f"{LICHESS_GAMES_EXPORT_URL}/{username}"
        
        params = {
            "pgnInJson": "true" if with_pgn else "false",
            "opening": "true" if with_opening else "false",
            "clocks": "false",
            "evals": "false",
            "moves": "true",
        }
        
        if since is not None:
            params["since"] = str(since)
        if until is not None:
            params["until"] = str(until)
        if max_games is not None:
            params["max"] = str(max_games)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/x-ndjson",
        }
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=None)) as client:
            async with client.stream("GET", url, params=params, headers=headers) as response:
                if response.status_code == 401:
                    raise LichessSyncError("Invalid or expired access token")
                if response.status_code == 404:
                    raise LichessSyncError(f"User '{username}' not found")
                if response.status_code == 429:
                    raise LichessSyncError("Rate limited by Lichess. Please try again later.")
                if response.status_code != 200:
                    raise LichessSyncError(f"Lichess API error: {response.status_code}")
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            import json
                            game_data = json.loads(line)
                            game = LichessGame.from_ndjson(game_data)
                            # Skip non-standard variants (antichess, atomic, etc.)
                            if game.variant not in ALLOWED_VARIANTS:
                                continue
                            yield game
                        except Exception as e:
                            # Skip malformed lines
                            continue
    
    async def sync_account(
        self,
        username: str,
        access_token: str,
        since: Optional[int] = None,
        on_game: Optional[Callable[[LichessGame, int], None]] = None,
        max_games: Optional[int] = None,
    ) -> SyncProgress:
        """
        Sync all games for an account.
        
        Args:
            username: Lichess username
            access_token: OAuth2 access token
            since: Unix timestamp (milliseconds) to sync from (for incremental sync)
            on_game: Callback function called for each game (game, index)
            max_games: Maximum number of games to sync
        
        Returns:
            SyncProgress with final status
        """
        username_lower = username.lower()
        
        # Initialize progress
        progress = SyncProgress(
            status=SyncStatus.STARTING,
            started_at=datetime.now(),
        )
        self._sync_progress[username_lower] = progress
        self._cancel_flags[username_lower] = False
        
        try:
            progress.status = SyncStatus.SYNCING
            games_list = []
            
            async for game in self.stream_games(
                username=username,
                access_token=access_token,
                since=since,
                max_games=max_games,
                with_opening=True,
            ):
                # Check for cancellation
                if self._cancel_flags.get(username_lower, False):
                    progress.status = SyncStatus.CANCELLED
                    break
                
                games_list.append(game)
                progress.synced_games = len(games_list)
                
                if on_game:
                    on_game(game, len(games_list))
            
            if progress.status != SyncStatus.CANCELLED:
                progress.status = SyncStatus.COMPLETED
                progress.total_games = len(games_list)
            
            progress.completed_at = datetime.now()
            
        except LichessSyncError as e:
            progress.status = SyncStatus.ERROR
            progress.error_message = str(e)
            progress.completed_at = datetime.now()
        except Exception as e:
            progress.status = SyncStatus.ERROR
            progress.error_message = f"Unexpected error: {str(e)}"
            progress.completed_at = datetime.now()
        
        return progress
    
    async def count_user_games(self, username: str, access_token: str) -> Optional[int]:
        """
        Get the total number of games for a user.
        
        Uses the Lichess API to get user stats.
        """
        url = f"{LICHESS_API_BASE}/user/{username}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    count = data.get("count", {})
                    return count.get("all", 0)
            except Exception:
                pass
        
        return None


# Singleton instance for tracking sync operations across requests
_sync_manager: Optional[LichessSync] = None


def get_sync_manager() -> LichessSync:
    """Get the global sync manager instance."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = LichessSync()
    return _sync_manager

