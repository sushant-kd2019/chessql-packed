"""
Natural Language Search Module for ChessQL

This module provides natural language to ChessQL query conversion using OpenAI.
"""

import os
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from query_language import ChessQueryLanguage

# Load environment variables from .env file
load_dotenv()


class NaturalLanguageSearch:
    """Handles natural language to ChessQL query conversion."""
    
    def __init__(self, db_path: str = "chess_games.db", api_key: Optional[str] = None):
        """Initialize the natural language search system."""
        self.query_lang = ChessQueryLanguage(db_path)
        
        # Get API key from parameter or environment
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=api_key)
        
        # System prompt for the AI
        self.system_prompt = """You are a ChessQL query generator. Convert natural language questions about chess games into SQL queries.

Available tables and fields:
- games: id, white_player, black_player, result, date_played, event, site, round, eco_code, opening, time_control, white_elo, black_elo, variant, termination, white_result, black_result, created_at
- captures: id, game_id, move_number, side, capturing_piece, captured_piece, from_square, to_square, move_notation, piece_value, captured_value, is_exchange, is_sacrifice, created_at

Special query patterns:
- Player results: Use (player_name won/lost/drew) for player outcomes
- Piece events: Use (piece exchanged/sacrificed) for piece exchanges/sacrifices
- Captures: Use (piece1 captured piece2) for specific captures
- Move conditions: Add "before move N" or "after move N" for timing
- Sorting: Add ORDER BY column [ASC/DESC] for sorting

Examples:
- "Show me games where lecorvus won" → SELECT * FROM games WHERE ("lecorvus" won)
- "Find games where queen was sacrificed" → SELECT * FROM games WHERE (queen sacrificed)
- "Show lecorvus wins with queen sacrifices" → SELECT * FROM games WHERE ("lecorvus" won) AND (queen sacrificed)
- "Find pawn exchanges before move 10" → SELECT * FROM games WHERE (pawn exchanged before move 10)
- "Show games sorted by ELO rating" → SELECT * FROM games ORDER BY CAST(white_elo AS INTEGER) DESC

Always return ONLY the SQL query, no explanations or additional text."""

    def search(self, natural_language_query: str) -> List[Dict[str, Any]]:
        """Convert natural language query to ChessQL and execute it."""
        try:
            # Convert natural language to SQL
            sql_query = self._convert_to_sql(natural_language_query)
            
            if not sql_query:
                return [{"error": "Could not convert natural language query to SQL"}]
            
            # Execute the SQL query
            results = self.query_lang.execute_query(sql_query)
            return results
            
        except Exception as e:
            return [{"error": f"Error processing query: {str(e)}"}]
    
    def _convert_to_sql(self, natural_language_query: str) -> Optional[str]:
        """Convert natural language query to SQL using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": natural_language_query}
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
    
    def get_example_queries(self) -> List[str]:
        """Get example natural language queries."""
        return [
            "Show me all games where lecorvus won",
            "Find games where the queen was sacrificed",
            "Show me lecorvus wins with queen sacrifices",
            "Find games where pawns were exchanged before move 10",
            "Show games sorted by ELO rating",
            "Find games where lecorvus lost and knight was sacrificed",
            "Show me the most recent games",
            "Find games with the highest ELO ratings",
            "Show me games where bishops were captured by knights",
            "Find games where lecorvus drew",
            "Show me games with queen exchanges after move 20",
            "Find games where rooks were sacrificed",
            "Show me games sorted by date",
            "Find games where lecorvus won and pawn was exchanged",
            "Show me games with the most captures"
        ]
