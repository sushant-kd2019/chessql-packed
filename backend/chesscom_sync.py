"""
Chess.com Game Sync Module
Handles syncing games from Chess.com API.
"""

import asyncio
import httpx
import re
from typing import Optional, Dict, Any, AsyncGenerator, Callable, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import time
import urllib.parse


# Chess.com API configuration
CHESSCOM_API_BASE = "https://api.chess.com/pub"
CHESSCOM_GAMES_ARCHIVES_URL = f"{CHESSCOM_API_BASE}/player"
CHESSCOM_USER_AGENT = "ChessQL/1.0 (https://github.com/yourusername/chessql)"

# Rate limiting: Serial requests are unlimited, but add small delay to be safe
REQUEST_DELAY = 0.2  # 200ms between requests

# Only allow standard chess variants
ALLOWED_RULES = ["chess"]


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


def extract_moves_from_pgn(pgn_text: str) -> str:
    """
    Extract move notation from PGN text.
    
    Args:
        pgn_text: Full PGN text with tags and moves
        
    Returns:
        Move notation string (e.g., "1. e4 e5 2. Nf3 Nc6 ...")
    """
    if not pgn_text:
        return ""
    
    lines = pgn_text.split('\n')
    moves = []
    
    for line in lines:
        line = line.strip()
        # Skip tag lines (lines starting with [)
        if line.startswith('['):
            continue
        # Skip empty lines
        if not line:
            continue
        # This should be move notation
        moves.append(line)
    
    # Join moves and clean up
    moves_text = " ".join(moves)
    # Remove result at the end if present (1-0, 0-1, 1/2-1/2, *)
    moves_text = re.sub(r'\s+(1-0|0-1|1/2-1/2|\*)\s*$', '', moves_text)
    
    return moves_text.strip()


def extract_game_id_from_url(url: str) -> str:
    """
    Extract game ID from Chess.com game URL.
    
    Args:
        url: Chess.com game URL (e.g., "https://www.chess.com/game/live/1234567890")
        
    Returns:
        Game ID string
    """
    if not url:
        return ""
    
    # Extract the last part of the URL path
    parts = url.rstrip('/').split('/')
    if parts:
        return parts[-1]
    return ""


def map_time_class_to_speed(time_class: str) -> str:
    """
    Map Chess.com time_class to internal speed category.
    
    Args:
        time_class: Chess.com time class (bullet, blitz, rapid, daily, classical)
        
    Returns:
        Speed category string
    """
    mapping = {
        "bullet": "bullet",
        "blitz": "blitz",
        "rapid": "rapid",
        "daily": "classical",  # Daily games treated as classical
        "classical": "classical",
    }
    return mapping.get(time_class.lower(), "")


def map_result_to_pgn_result(white_result: str, black_result: str) -> str:
    """
    Map Chess.com result codes to PGN result format.
    
    Args:
        white_result: White player result (win, loss, checkmated, etc.)
        black_result: Black player result (win, loss, checkmated, etc.)
        
    Returns:
        PGN result string (1-0, 0-1, 1/2-1/2, or *)
    """
    if white_result == "win" or black_result == "checkmated" or black_result == "resigned":
        return "1-0"
    elif black_result == "win" or white_result == "checkmated" or white_result == "resigned":
        return "0-1"
    elif white_result == "agreed" or black_result == "agreed" or white_result == "repetition" or black_result == "repetition":
        return "1/2-1/2"
    elif white_result == "timeout" and black_result != "win":
        return "0-1"
    elif black_result == "timeout" and white_result != "win":
        return "1-0"
    else:
        return "1/2-1/2"  # Default to draw for other cases


@dataclass
class ChessComGame:
    """Parsed Chess.com game data."""
    id: str  # Game ID extracted from URL
    url: str  # Full game URL
    pgn: str  # Full PGN text
    moves: str  # Extracted move notation
    end_time: int  # Unix timestamp in seconds
    time_control: str  # Time control string (e.g., "600+0")
    time_class: str  # Time class (bullet, blitz, rapid, etc.)
    white_player: str
    black_player: str
    white_rating: Optional[int]
    black_rating: Optional[int]
    white_result: str  # Chess.com result code
    black_result: str  # Chess.com result code
    result: str  # PGN result (1-0, 0-1, 1/2-1/2)
    rules: str  # Game rules (usually "chess")
    rated: bool
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "ChessComGame":
        """Parse a Chess.com game JSON object."""
        white = data.get("white", {})
        black = data.get("black", {})
        
        # Extract game ID from URL
        url = data.get("url", "")
        game_id = extract_game_id_from_url(url)
        
        # Extract moves from PGN
        pgn = data.get("pgn", "")
        moves = extract_moves_from_pgn(pgn)
        
        # Map results
        white_result = white.get("result", "")
        black_result = black.get("result", "")
        result = map_result_to_pgn_result(white_result, black_result)
        
        # Map time class to speed
        time_class = data.get("time_class", "")
        speed = map_time_class_to_speed(time_class)
        
        return cls(
            id=game_id,
            url=url,
            pgn=pgn,
            moves=moves,
            end_time=data.get("end_time", 0),
            time_control=data.get("time_control", ""),
            time_class=time_class,
            white_player=white.get("username", "Anonymous"),
            black_player=black.get("username", "Anonymous"),
            white_rating=white.get("rating"),
            black_rating=black.get("rating"),
            white_result=white_result,
            black_result=black_result,
            result=result,
            rules=data.get("rules", "chess"),
            rated=data.get("rated", False),
        )
    
    def to_pgn_dict(self) -> Dict[str, Any]:
        """Convert to the format expected by ChessDatabase.insert_game()."""
        # Convert timestamp from seconds to date string
        date_str = datetime.fromtimestamp(self.end_time).strftime("%Y.%m.%d")
        
        # Build PGN text if not already present
        if self.pgn:
            pgn_text = self.pgn
        else:
            # Build PGN from components
            pgn_lines = [
                f'[Event "Chess.com {self.time_class.capitalize()} Game"]',
                f'[Site "{self.url}"]',
                f'[Date "{date_str}"]',
                f'[White "{self.white_player}"]',
                f'[Black "{self.black_player}"]',
                f'[Result "{self.result}"]',
            ]
            
            if self.white_rating:
                pgn_lines.append(f'[WhiteElo "{self.white_rating}"]')
            if self.black_rating:
                pgn_lines.append(f'[BlackElo "{self.black_rating}"]')
            if self.time_control:
                pgn_lines.append(f'[TimeControl "{self.time_control}"]')
            if self.rules != "chess":
                pgn_lines.append(f'[Variant "{self.rules.capitalize()}"]')
            
            pgn_lines.append("")
            pgn_lines.append(f"{self.moves} {self.result}")
            pgn_text = "\n".join(pgn_lines)
        
        return {
            "chesscom_id": self.id,
            "pgn_text": pgn_text,
            "moves": self.moves,
            "white_player": self.white_player,
            "black_player": self.black_player,
            "result": self.result,
            "date_played": date_str,
            "event": f"Chess.com {self.time_class.capitalize()} Game",
            "site": self.url,
            "round": "-",
            "eco_code": "",  # Chess.com doesn't provide ECO in monthly archive
            "opening": "",  # Chess.com doesn't provide opening in monthly archive
            "time_control": self.time_control,
            "white_elo": str(self.white_rating) if self.white_rating else "",
            "black_elo": str(self.black_rating) if self.black_rating else "",
            "variant": self.rules,
            "termination": self.white_result if self.white_result != "win" else self.black_result,
            "speed": map_time_class_to_speed(self.time_class),
        }


class ChessComSyncError(Exception):
    """Custom exception for sync errors."""
    pass


class ChessComSync:
    """Handles syncing games from Chess.com API."""
    
    def __init__(self):
        """Initialize the sync handler."""
        # Track sync progress per username
        self._sync_progress: Dict[str, SyncProgress] = {}
        self._cancel_flags: Dict[str, bool] = {}
    
    def get_progress(self, username: str) -> SyncProgress:
        """Get sync progress for a user."""
        return self._sync_progress.get(username.lower(), SyncProgress())
    
    def cancel_sync(self, username: str) -> bool:
        """Request cancellation of a sync operation."""
        if username.lower() in self._sync_progress:
            self._cancel_flags[username.lower()] = True
            return True
        return False
    
    def is_syncing(self, username: str) -> bool:
        """Check if a sync is in progress for a user."""
        progress = self._sync_progress.get(username.lower())
        return progress is not None and progress.status == SyncStatus.SYNCING
    
    async def get_archives(self, username: str) -> List[str]:
        """
        Get list of available monthly archive URLs for a user.
        
        Args:
            username: Chess.com username
            
        Returns:
            List of archive URLs (e.g., ["/player/username/games/2024/01", ...])
        """
        url = f"{CHESSCOM_GAMES_ARCHIVES_URL}/{username}/games/archives"
        
        headers = {
            "User-Agent": CHESSCOM_USER_AGENT,
            "Accept": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            try:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 404:
                    raise ChessComSyncError(f"User '{username}' not found")
                if response.status_code == 429:
                    raise ChessComSyncError("Rate limited by Chess.com. Please try again later.")
                if response.status_code != 200:
                    raise ChessComSyncError(f"Chess.com API error: {response.status_code}")
                
                data = response.json()
                archives = data.get("archives", [])
                return archives
                
            except httpx.HTTPError as e:
                raise ChessComSyncError(f"Network error: {str(e)}")
    
    async def stream_games(
        self,
        username: str,
        since: Optional[int] = None,
        until: Optional[int] = None,
        max_games: Optional[int] = None,
    ) -> AsyncGenerator[ChessComGame, None]:
        """
        Stream games from Chess.com API by iterating through monthly archives.
        
        Args:
            username: Chess.com username
            since: Unix timestamp (seconds) to fetch games from
            until: Unix timestamp (seconds) to fetch games until
            max_games: Maximum number of games to fetch
        
        Yields:
            ChessComGame objects
        """
        # Get list of archives
        try:
            archives = await self.get_archives(username)
        except ChessComSyncError:
            raise
        
        # Filter archives by date if since/until provided
        filtered_archives = []
        for archive_url in archives:
            # Archive URL format: /player/{username}/games/{year}/{month}
            # Extract year and month to check if we should process this archive
            if since or until:
                parts = archive_url.rstrip('/').split('/')
                if len(parts) >= 2:
                    try:
                        year = int(parts[-2])
                        month = int(parts[-1])
                        archive_start = int(datetime(year, month, 1).timestamp())
                        # Approximate archive end (next month start)
                        if month == 12:
                            archive_end = int(datetime(year + 1, 1, 1).timestamp())
                        else:
                            archive_end = int(datetime(year, month + 1, 1).timestamp())
                        
                        # Check if archive overlaps with requested time range
                        if since and archive_end < since:
                            continue
                        if until and archive_start > until:
                            continue
                    except (ValueError, IndexError):
                        pass  # Include archive if we can't parse it
            
            filtered_archives.append(archive_url)
        
        # Process archives in reverse order (newest first)
        filtered_archives.reverse()
        
        headers = {
            "User-Agent": CHESSCOM_USER_AGENT,
            "Accept": "application/json",
        }
        
        games_count = 0
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            for archive_url in filtered_archives:
                # Check for cancellation
                if self._cancel_flags.get(username.lower(), False):
                    break
                
                # Check max games limit
                if max_games and games_count >= max_games:
                    break
                
                # Construct full URL (archive_url might already be full URL or relative path)
                if archive_url.startswith("http"):
                    full_url = archive_url
                else:
                    full_url = f"{CHESSCOM_API_BASE}{archive_url}"
                
                try:
                    response = await client.get(full_url, headers=headers)
                    
                    if response.status_code == 404:
                        # Archive doesn't exist, skip
                        continue
                    if response.status_code == 429:
                        # Rate limited, wait and retry
                        await asyncio.sleep(5)
                        response = await client.get(full_url, headers=headers)
                        if response.status_code != 200:
                            continue
                    if response.status_code != 200:
                        # Skip this archive
                        continue
                    
                    data = response.json()
                    games = data.get("games", [])
                    
                    # Process games in reverse order (newest first)
                    for game_data in reversed(games):
                        # Check for cancellation
                        if self._cancel_flags.get(username.lower(), False):
                            break
                        
                        # Check max games limit
                        if max_games and games_count >= max_games:
                            break
                        
                        # Filter by date if needed
                        end_time = game_data.get("end_time", 0)
                        if since and end_time < since:
                            continue
                        if until and end_time > until:
                            continue
                        
                        # Filter by rules (only standard chess)
                        rules = game_data.get("rules", "chess")
                        if rules not in ALLOWED_RULES:
                            continue
                        
                        try:
                            game = ChessComGame.from_json(game_data)
                            yield game
                            games_count += 1
                        except Exception as e:
                            # Skip malformed games
                            continue
                    
                    # Rate limiting delay
                    await asyncio.sleep(REQUEST_DELAY)
                    
                except Exception as e:
                    # Skip this archive on error
                    continue
    
    async def sync_account(
        self,
        username: str,
        since: Optional[int] = None,
        on_game: Optional[Callable[[ChessComGame, int], None]] = None,
        max_games: Optional[int] = None,
    ) -> SyncProgress:
        """
        Sync all games for an account.
        
        Args:
            username: Chess.com username
            since: Unix timestamp (seconds) to sync from (for incremental sync)
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
                since=since,
                max_games=max_games,
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
            
        except ChessComSyncError as e:
            progress.status = SyncStatus.ERROR
            progress.error_message = str(e)
            progress.completed_at = datetime.now()
        except Exception as e:
            progress.status = SyncStatus.ERROR
            progress.error_message = f"Unexpected error: {str(e)}"
            progress.completed_at = datetime.now()
        
        return progress


# Singleton instance for tracking sync operations across requests
_sync_manager: Optional[ChessComSync] = None


def get_sync_manager() -> ChessComSync:
    """Get the global sync manager instance."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = ChessComSync()
    return _sync_manager

