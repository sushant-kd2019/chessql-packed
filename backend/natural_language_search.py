"""
Natural Language Search Module for ChessQL

This module provides natural language to ChessQL query conversion using OpenAI.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from query_language import ChessQueryLanguage

# Load environment variables from multiple locations (for packaged app support)
def _load_env_files():
    """Load .env files from multiple possible locations."""
    # Priority order (first found wins for each variable):
    # 1. Already set environment variables
    # 2. .env in current directory (development)
    # 3. .env in user's Application Support/ChessQL (packaged app)
    # 4. .env in user's home/.chessql (fallback)
    
    env_locations = [
        Path.cwd() / '.env',  # Development
        Path.home() / 'Library' / 'Application Support' / 'ChessQL' / '.env',  # macOS packaged
        Path.home() / '.config' / 'chessql' / '.env',  # Linux
        Path.home() / '.chessql' / '.env',  # Fallback
    ]
    
    for env_path in env_locations:
        if env_path.exists():
            load_dotenv(env_path, override=False)  # Don't override existing vars

_load_env_files()


class NaturalLanguageSearch:
    """Handles natural language to ChessQL query conversion."""
    
    def __init__(self, db_path: str = "chess_games.db", api_key: Optional[str] = None, reference_player: str = "lecorvus"):
        """Initialize the natural language search system."""
        self.db_path = db_path
        self.reference_player = reference_player
        self.query_lang = ChessQueryLanguage(db_path, reference_player)
        
        # Get API key from parameter or environment
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=api_key)
        
        # System prompt for the AI (using default reference player)
        self.system_prompt = self._generate_system_prompt(reference_player)
        
        # Legacy system prompt kept for reference
        self._legacy_system_prompt = f"""You are a ChessQL query generator. Convert natural language questions about chess games into SQL queries.

CRITICAL RULES:
1. ALWAYS query the 'games' table, NEVER the 'captures' table directly
2. Use EXACT syntax patterns shown in examples - no variations
3. For player results: (player_name won/lost/drew) - NO quotes around player names
4. For piece events: (piece_name exchanged/sacrificed) - NO player names in piece events
5. For counts: SELECT COUNT(*) FROM games WHERE conditions
6. Combine conditions with AND/OR as needed
7. NEVER use JOIN with captures table - use ChessQL patterns like (queen sacrificed) instead
8. For player-specific sacrifices: combine (player won/lost) AND (piece sacrificed) patterns
9. Reference player is '{reference_player}' - use this for opponent queries
10. For ELO ratings: Use white_elo or black_elo columns, NOT player_elo. Check both white_player and black_player to determine which ELO column to use
11. For pawn promotions: Use (pawn promoted to piece) syntax, NOT (player piece promoted). When player promotes, combine (player won) AND (pawn promoted to piece)
12. For game speed/time control type: Use the 'speed' column with values: 'ultraBullet', 'bullet', 'blitz', 'rapid', 'classical'

Available tables and fields:
- games: id, white_player, black_player, result, date_played, event, site, round, eco_code, opening, time_control, white_elo, black_elo, variant, termination, white_result, black_result, speed, created_at
- captures: id, game_id, move_number, side, capturing_piece, captured_piece, from_square, to_square, move_notation, piece_value, captured_value, is_exchange, is_sacrifice, created_at

The 'speed' column contains the game time control category:
- 'ultraBullet' (≤29s estimated duration)
- 'bullet' (≤179s)
- 'blitz' (≤479s)
- 'rapid' (≤1499s)
- 'classical' (≥1500s)

Special query patterns:
- Player results: (player_name won/lost/drew) for player outcomes
- Piece events: (piece exchanged/sacrificed) for piece exchanges/sacrifices
- Captures: (piece1 captured piece2) for specific captures
- Pawn promotions: (pawn promoted to piece) for pawn promotions
- Move conditions: Add "before move N" or "after move N" for timing
- Sorting: Add ORDER BY column [ASC/DESC] for sorting
- Game speed: Use speed = 'blitz' (or bullet/rapid/classical/ultraBullet) for filtering by time control type

EXAMPLES:
- "Show me games where {reference_player} won" → SELECT * FROM games WHERE ({reference_player} won)
- "Find games where queen was sacrificed" → SELECT * FROM games WHERE (queen sacrificed)
- "How many games did {reference_player} sacrifice his queen" → SELECT COUNT(*) FROM games WHERE ({reference_player} queen sacrificed)
- "Count games where queen was sacrificed" → SELECT COUNT(*) FROM games WHERE (queen sacrificed)
- "How many games did {reference_player} sacrifice his queen and win" → SELECT COUNT(*) FROM games WHERE ({reference_player} won) AND ({reference_player} queen sacrificed)
- "How many games did {reference_player} sacrifice his queen and lose" → SELECT COUNT(*) FROM games WHERE ({reference_player} lost) AND ({reference_player} queen sacrificed)
- "Show games where {reference_player} sacrificed his queen and won" → SELECT * FROM games WHERE ({reference_player} won) AND ({reference_player} queen sacrificed)
- "Find games where opponent sacrificed their queen" → SELECT * FROM games WHERE (opponent queen sacrificed)
- "Show games where opponent sacrificed queen and {reference_player} won" → SELECT * FROM games WHERE ({reference_player} won) AND (opponent queen sacrificed)
- "Show {reference_player} wins with queen sacrifices" → SELECT * FROM games WHERE ({reference_player} won) AND (queen sacrificed)
- "Find pawn exchanges before move 10" → SELECT * FROM games WHERE (pawn exchanged before move 10)
- "Show games sorted by ELO rating" → SELECT * FROM games ORDER BY CAST(white_elo AS INTEGER) DESC
- "Find games where knight was exchanged" → SELECT * FROM games WHERE (knight exchanged)
- "Show me {reference_player} losses" → SELECT * FROM games WHERE ({reference_player} lost)
- "Count games with bishop sacrifices" → SELECT COUNT(*) FROM games WHERE (bishop sacrificed)
- "How many games did {reference_player} sacrifice his knight" → SELECT COUNT(*) FROM games WHERE ({reference_player} won) AND (knight sacrificed)
- "Show games where {reference_player} won and sacrificed queen" → SELECT * FROM games WHERE ({reference_player} won) AND (queen sacrificed)
- "Games where {reference_player} was rated over 1500" → SELECT * FROM games WHERE ((white_player = '{reference_player}' AND CAST(white_elo AS INTEGER) > 1500) OR (black_player = '{reference_player}' AND CAST(black_elo AS INTEGER) > 1500))
- "Count games where {reference_player} sacrificed queen and lost when rated over 1500" → SELECT COUNT(*) FROM games WHERE ({reference_player} lost) AND ({reference_player} queen sacrificed) AND ((white_player = '{reference_player}' AND CAST(white_elo AS INTEGER) > 1500) OR (black_player = '{reference_player}' AND CAST(black_elo AS INTEGER) > 1500))
- "Find games where pawn was promoted to queen" → SELECT * FROM games WHERE (pawn promoted to queen)
- "Count games with pawn promotions to knight" → SELECT COUNT(*) FROM games WHERE (pawn promoted to knight)
- "Show games where {reference_player} promoted pawn to queen" → SELECT * FROM games WHERE ({reference_player} won) AND (pawn promoted to queen)
- "Find games with pawn promotions before move 30" → SELECT * FROM games WHERE (pawn promoted to queen before move 30)
- "Show site from games where {reference_player} promoted to a knight" → SELECT site FROM games WHERE ({reference_player} won) AND (pawn promoted to knight)
- "Games where {reference_player} promoted to queen" → SELECT * FROM games WHERE ({reference_player} won) AND (pawn promoted to queen)
- "Count games where {reference_player} promoted to rook" → SELECT COUNT(*) FROM games WHERE ({reference_player} won) AND (pawn promoted to rook)
- "Games where {reference_player} promoted to queen twice" → SELECT * FROM games WHERE ({reference_player} won) AND (pawn promoted to queen x 2)
- "Show site from games where {reference_player} promoted to queen twice" → SELECT site FROM games WHERE ({reference_player} won) AND (pawn promoted to queen x 2)
- "Count games where {reference_player} promoted to queen x 3" → SELECT COUNT(*) FROM games WHERE ({reference_player} won) AND (pawn promoted to queen x 3)
- "Find games where pawn was promoted to knight x 2" → SELECT * FROM games WHERE (pawn promoted to knight x 2)
- "Show {reference_player} blitz games" → SELECT * FROM games WHERE ({reference_player} won OR {reference_player} lost OR {reference_player} drew) AND speed = 'blitz'
- "How many bullet games did {reference_player} win" → SELECT COUNT(*) FROM games WHERE ({reference_player} won) AND speed = 'bullet'
- "Show all rapid games" → SELECT * FROM games WHERE speed = 'rapid'
- "Count {reference_player} wins in blitz" → SELECT COUNT(*) FROM games WHERE ({reference_player} won) AND speed = 'blitz'
- "{reference_player} classical games where queen was sacrificed" → SELECT * FROM games WHERE ({reference_player} won OR {reference_player} lost OR {reference_player} drew) AND speed = 'classical' AND (queen sacrificed)
- "Show games by speed category" → SELECT speed, COUNT(*) as count FROM games GROUP BY speed

Always return ONLY the SQL query, no explanations or additional text."""

    def search(self, natural_language_query: str, show_query: bool = True, reference_player: Optional[str] = None) -> List[Dict[str, Any]]:
        """Convert natural language query to ChessQL and execute it.
        
        Args:
            natural_language_query: The user's question in natural language
            show_query: Whether to print the generated SQL query
            reference_player: Optional player name to use as context for "I", "my", etc.
                             If not provided, uses the default reference player.
        """
        try:
            # Convert natural language to SQL with optional reference player override
            sql_query = self._convert_to_sql(natural_language_query, reference_player)
            
            if not sql_query:
                return [{"error": "Could not convert natural language query to SQL"}]
            
            # Show the generated SQL query if requested
            if show_query:
                print(f"Generated SQL: {sql_query}")
                print("-" * 50)
            
            # Execute the SQL query using the appropriate reference player
            if reference_player:
                # Create a temporary query_lang instance with the specified reference player
                from query_language import ChessQueryLanguage
                temp_query_lang = ChessQueryLanguage(self.query_lang.db_path, reference_player)
                results = temp_query_lang.execute_query(sql_query)
            else:
                results = self.query_lang.execute_query(sql_query)
            
            return results
            
        except Exception as e:
            return [{"error": f"Error processing query: {str(e)}"}]
    
    def _convert_to_sql(self, natural_language_query: str, reference_player: Optional[str] = None) -> Optional[str]:
        """Convert natural language query to SQL using OpenAI.
        
        Args:
            natural_language_query: The user's question
            reference_player: Optional player name to override the default reference player
        """
        try:
            # Use override player or default
            player = reference_player or self.reference_player
            
            # Generate prompt with the appropriate reference player
            system_prompt = self._generate_system_prompt(player)
            
            # Add context about who is asking if a specific player is selected
            user_message = natural_language_query
            if reference_player:
                user_message = f"[Context: The user is asking about their account '{reference_player}'. When they say 'I', 'my', 'me', they mean '{reference_player}'.]\n\n{natural_language_query}"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the response (remove any markdown formatting)
            sql_query = re.sub(r'^```sql\s*', '', sql_query)
            sql_query = re.sub(r'\s*```$', '', sql_query)
            
            return sql_query
            
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return None
    
    def _generate_system_prompt(self, reference_player: str) -> str:
        """Generate the system prompt with the specified reference player."""
        return f"""You are a ChessQL query generator. Convert natural language questions about chess games into SQL queries.

CRITICAL RULES:
1. ALWAYS query the 'games' table, NEVER the 'captures' table directly
2. Use EXACT syntax patterns shown in examples - no variations
3. For player results: (player_name won/lost/drew) - NO quotes around player names
4. For piece events: (piece_name exchanged/sacrificed) - NO player names in piece events
5. For counts: SELECT COUNT(*) FROM games WHERE conditions
6. Combine conditions with AND/OR as needed
7. NEVER use JOIN with captures table - use ChessQL patterns like (queen sacrificed) instead
8. For player-specific sacrifices: combine (player won/lost) AND (piece sacrificed) patterns
9. Reference player is '{reference_player}' - when user says "I", "my", "me", they mean this player
10. For ELO ratings: Use white_elo or black_elo columns, NOT player_elo. Check both white_player and black_player to determine which ELO column to use
11. For pawn promotions: Use (pawn promoted to piece) syntax, NOT (player piece promoted). When player promotes, combine (player won) AND (pawn promoted to piece)
12. For game speed/time control type: Use the 'speed' column with values: 'ultraBullet', 'bullet', 'blitz', 'rapid', 'classical'

Available tables and fields:
- games: id, white_player, black_player, result, date_played, event, site, round, eco_code, opening, time_control, white_elo, black_elo, variant, termination, white_result, black_result, speed, created_at
- captures: id, game_id, move_number, side, capturing_piece, captured_piece, from_square, to_square, move_notation, piece_value, captured_value, is_exchange, is_sacrifice, created_at

The 'speed' column contains the game time control category:
- 'ultraBullet' (≤29s estimated duration)
- 'bullet' (≤179s)
- 'blitz' (≤479s)
- 'rapid' (≤1499s)
- 'classical' (≥1500s)

The 'variant' column contains the chess variant:
- 'standard' - Normal chess
- 'chess960' - Fischer Random Chess (randomized starting position)
Note: Other variants like antichess, atomic, crazyhouse are filtered out during sync.

Special query patterns:
- Player results: (player_name won/lost/drew) for player outcomes
- Piece events: (piece exchanged/sacrificed) for piece exchanges/sacrifices
- Captures: (piece1 captured piece2) for specific captures
- Pawn promotions: (pawn promoted to piece) for pawn promotions
- Move conditions: Add "before move N" or "after move N" for timing
- Sorting: Add ORDER BY column [ASC/DESC] for sorting
- Game speed: Use speed = 'blitz' (or bullet/rapid/classical/ultraBullet) for filtering by time control type
- Game variant: Use variant = 'standard' or variant = 'chess960' for filtering by variant

EXAMPLES:
- "Show me games where {reference_player} won" → SELECT * FROM games WHERE ({reference_player} won)
- "my wins" → SELECT * FROM games WHERE ({reference_player} won)
- "games I lost" → SELECT * FROM games WHERE ({reference_player} lost)
- "Find games where queen was sacrificed" → SELECT * FROM games WHERE (queen sacrificed)
- "How many games did I sacrifice my queen" → SELECT COUNT(*) FROM games WHERE ({reference_player} queen sacrificed)
- "Count games where queen was sacrificed" → SELECT COUNT(*) FROM games WHERE (queen sacrificed)
- "How many games did I sacrifice my queen and win" → SELECT COUNT(*) FROM games WHERE ({reference_player} won) AND ({reference_player} queen sacrificed)
- "Show games where I sacrificed queen and won" → SELECT * FROM games WHERE ({reference_player} won) AND ({reference_player} queen sacrificed)
- "Find games where opponent sacrificed their queen" → SELECT * FROM games WHERE (opponent queen sacrificed)
- "my wins with queen sacrifices" → SELECT * FROM games WHERE ({reference_player} won) AND (queen sacrificed)
- "Find pawn exchanges before move 10" → SELECT * FROM games WHERE (pawn exchanged before move 10)
- "Show games sorted by ELO rating" → SELECT * FROM games ORDER BY CAST(white_elo AS INTEGER) DESC
- "Show my losses" → SELECT * FROM games WHERE ({reference_player} lost)
- "Count my bishop sacrifices" → SELECT COUNT(*) FROM games WHERE ({reference_player} bishop sacrificed)
- "Games where I was rated over 1500" → SELECT * FROM games WHERE ((white_player = '{reference_player}' AND CAST(white_elo AS INTEGER) > 1500) OR (black_player = '{reference_player}' AND CAST(black_elo AS INTEGER) > 1500))
- "Find games where I promoted pawn to queen" → SELECT * FROM games WHERE ({reference_player} won) AND (pawn promoted to queen)
- "Show my blitz games" → SELECT * FROM games WHERE ({reference_player} won OR {reference_player} lost OR {reference_player} drew) AND speed = 'blitz'
- "How many bullet games did I win" → SELECT COUNT(*) FROM games WHERE ({reference_player} won) AND speed = 'bullet'
- "Show all rapid games" → SELECT * FROM games WHERE speed = 'rapid'
- "Count my wins in blitz" → SELECT COUNT(*) FROM games WHERE ({reference_player} won) AND speed = 'blitz'
- "My classical games where I sacrificed a queen" → SELECT * FROM games WHERE ({reference_player} won OR {reference_player} lost OR {reference_player} drew) AND speed = 'classical' AND (queen sacrificed)
- "Show games by speed category" → SELECT speed, COUNT(*) as count FROM games GROUP BY speed
- "My win rate in bullet vs blitz" → SELECT speed, COUNT(*) as total, SUM(CASE WHEN ({reference_player} won) THEN 1 ELSE 0 END) as wins FROM games WHERE speed IN ('bullet', 'blitz') GROUP BY speed
- "Find my rapid losses" → SELECT * FROM games WHERE ({reference_player} lost) AND speed = 'rapid'
- "Show my chess960 games" → SELECT * FROM games WHERE ({reference_player} won OR {reference_player} lost OR {reference_player} drew) AND variant = 'chess960'
- "How many standard games have I won" → SELECT COUNT(*) FROM games WHERE ({reference_player} won) AND variant = 'standard'
- "Show games by variant" → SELECT variant, COUNT(*) as count FROM games GROUP BY variant
- "My chess960 wins" → SELECT * FROM games WHERE ({reference_player} won) AND variant = 'chess960'
- "Standard blitz games I won" → SELECT * FROM games WHERE ({reference_player} won) AND variant = 'standard' AND speed = 'blitz'

Always return ONLY the SQL query, no explanations or additional text."""
    
    def get_example_queries(self) -> List[str]:
        """Get example natural language queries."""
        return [
            f"Show me all games where {self.reference_player} won",
            "Find games where the queen was sacrificed",
            f"Show me {self.reference_player} wins with queen sacrifices",
            "Find games where pawns were exchanged before move 10",
            "Show games sorted by ELO rating",
            f"Find games where {self.reference_player} lost and knight was sacrificed",
            "Show me the most recent games",
            "Find games with the highest ELO ratings",
            "Show me games where bishops were captured by knights",
            f"Find games where {self.reference_player} drew",
            "Show me games with queen exchanges after move 20",
            "Find games where rooks were sacrificed",
            "Show me games sorted by date",
            f"Find games where {self.reference_player} won and pawn was exchanged",
            "Show me games with the most captures",
            # Speed/time control examples
            "Show me all my blitz games",
            f"How many bullet games did {self.reference_player} win",
            "Show all rapid games",
            f"Count {self.reference_player} wins in classical",
            "Show games by speed category",
            f"My blitz games where I sacrificed a queen",
            # Variant examples
            "Show my chess960 games",
            f"How many standard games did {self.reference_player} win",
            "Show games by variant",
            "My chess960 wins",
        ]
